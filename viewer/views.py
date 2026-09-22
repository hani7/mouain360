from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import json

from viewer.utils import generate_qr_code
from floor_plan.models import FloorPlan
from .models import Image, House, Room, RoomConnection, MissionParty, MissionDocument, MissionMedia
from .forms import ImageUploadForm, HouseForm, RoomForm, RoomConnectionForm

# ===== Dashboard View =====

@login_required
def dashboard(request):
    """Main dashboard showing user stats and recent activity."""
    from datetime import date, timedelta
    today = date.today()
    next_week = today + timedelta(days=7)

    # Metrics
    house_count_in_progress = House.objects.filter(owner=request.user, status='En cours').count()
    house_count_completed = House.objects.filter(owner=request.user, status='Achevé').count()
    house_count_late = House.objects.filter(owner=request.user, status='En retard').count()
    house_count_near_deadline = House.objects.filter(
        owner=request.user, 
        deadline__gte=today, 
        deadline__lte=next_week
    ).count()
    
    room_count = Room.objects.filter(house__owner=request.user).count()
    floorplan_count = FloorPlan.objects.filter(owner=request.user).count()
    
    # Recent activity for table
    recent_houses = House.objects.filter(owner=request.user).order_by('-created_at')[:5]
    
    # Alerts (projects near deadline or late)
    alerts = House.objects.filter(
        owner=request.user,
        deadline__isnull=False
    ).exclude(status='Achevé').order_by('deadline')[:3]

    # Recent Activity Feed
    recent_rooms = Room.objects.filter(house__owner=request.user).order_by('-uploaded_at')[:3]
    
    context = {
        'house_count_in_progress': house_count_in_progress,
        'house_count_completed': house_count_completed,
        'house_count_late': house_count_late,
        'house_count_near_deadline': house_count_near_deadline,
        'room_count': room_count,
        'floorplan_count': floorplan_count,
        'recent_houses': recent_houses,
        'alerts': alerts,
        'recent_rooms': recent_rooms,
        'today': today,
    }
    return render(request, 'dashboard.html', context)

@login_required
def calendar_view(request):
    """View for displaying missions in a calendar"""
    houses = House.objects.filter(owner=request.user)
    
    # We will pass the houses to the template, and let JS render them on a calendar
    # We serialize the relevant data to JSON so FullCalendar (or custom JS) can read it
    events = []
    for house in houses:
        if house.created_at:
            events.append({
                'title': house.name,
                'start': house.created_at.strftime('%Y-%m-%d'),
                'url': f'/viewer/house/{house.id}/',
                'color': '#01edfe', # primary color
                'textColor': '#000000',
            })
            
    context = {
        'events_json': json.dumps(events)
    }
    return render(request, 'calendar.html', context)

# ===== Original Image Viewer Views =====

@login_required
def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.owner = request.user
            image.save()
            return redirect('view_images')
    else:
        form = ImageUploadForm()
    return render(request, 'upload.html', {'form': form})

@login_required
def view_images(request):
    images = Image.objects.filter(owner=request.user)
    return render(request, 'view_images.html', {'images': images})

@login_required
def view_360_image(request, image_id):
    image = get_object_or_404(Image, id=image_id, owner=request.user)
    return render(request, 'view_360_image.html', {'image': image})

@login_required
def delete_image(request, image_id):
    image = get_object_or_404(Image, id=image_id, owner=request.user)
    image.delete()
    return redirect('view_images')

@login_required
def download_qr_code(request, image_id):
    """Generates the QR code for a given image and allows the user to download it."""
    image = get_object_or_404(Image, id=image_id, owner=request.user)
    image_url = request.build_absolute_uri(image.image.url)
    qr_code = generate_qr_code(image_url)
    response = HttpResponse(qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_code_{image_id}.png"'
    return response

@login_required
def download_house_qr_code(request, house_id):
    """Generates QR code for house walkthrough URL"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    from django.urls import reverse
    walkthrough_url = request.build_absolute_uri(reverse('public_tour', args=[house.share_token]))
    qr_code = generate_qr_code(walkthrough_url)
    response = HttpResponse(qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="house_{house.name}_qr.png"'
    return response

# ===== House Walkthrough Views =====

@login_required
def house_list(request):
    """List all houses with virtual walkthroughs"""
    houses = House.objects.filter(owner=request.user)
    return render(request, 'house_list.html', {'houses': houses})

@login_required
def create_house(request):
    """Create a new mission (house)"""
    if request.method == 'POST':
        # Create house
        house = House(
            owner=request.user,
            name=request.POST.get('name', ''),
            official_title=request.POST.get('official_title', ''),
            reference=request.POST.get('reference', ''),
            mission_type=request.POST.get('mission_type', 'Visite 360'),
            order_date=request.POST.get('order_date') or None,
            reception_date=request.POST.get('reception_date') or None,
            start_date=request.POST.get('start_date') or None,
            deadline=request.POST.get('deadline') or None,
            client=request.POST.get('client', ''),
            address=request.POST.get('address', ''),
            wilaya=request.POST.get('wilaya', ''),
            commune=request.POST.get('commune', '')
        )
        house.save()
        
        # Process parties
        party_names = request.POST.getlist('party_name[]')
        party_roles = request.POST.getlist('party_role[]')
        for name, role in zip(party_names, party_roles):
            if name and role:
                MissionParty.objects.create(house=house, name=name, role=role)
                
        # Process documents
        for doc_file in request.FILES.getlist('documents[]'):
            MissionDocument.objects.create(house=house, file=doc_file, name=doc_file.name)
            
        # Process plans
        for plan_file in request.FILES.getlist('plans[]'):
            # Just store the first one in floor_plan_image for now as it's built-in
            # If they upload multiple, it overwrites. A dedicated model is better for multiple.
            house.floor_plan_image = plan_file
            house.save()
            
        # Process medias (360 rooms)
        for media_file in request.FILES.getlist('medias[]'):
            Room.objects.create(house=house, image=media_file, title=media_file.name.split('.')[0])
        if request.POST.get('action') == 'save_and_stay':
            return JsonResponse({'status': 'success', 'house_id': house.id})
            
        return redirect('house_detail', house_id=house.id)
    return render(request, 'create_house.html')

@login_required
def edit_house(request, house_id):
    house = get_object_or_404(House, id=house_id, owner=request.user)
    if request.method == 'POST':
        house.name = request.POST.get('name', house.name)
        house.official_title = request.POST.get('official_title', house.official_title)
        house.reference = request.POST.get('reference', house.reference)
        house.mission_type = request.POST.get('mission_type', house.mission_type)
        house.client = request.POST.get('client', house.client)
        house.address = request.POST.get('address', house.address)
        house.wilaya = request.POST.get('wilaya', house.wilaya)
        house.commune = request.POST.get('commune', house.commune)
        
        # Dates - parse them correctly if they exist
        for date_field in ['start_date', 'deadline', 'order_date', 'reception_date']:
            val = request.POST.get(date_field)
            if val:
                setattr(house, date_field, val)
                
        house.save()
        
        # Process parties (since the form sends all parties, we replace them to avoid duplicates)
        party_names = request.POST.getlist('party_name[]')
        party_roles = request.POST.getlist('party_role[]')
        if 'party_name[]' in request.POST:
            house.parties.all().delete()
            for name, role in zip(party_names, party_roles):
                if name and role:
                    MissionParty.objects.create(house=house, name=name, role=role)
                    
        # Process documents
        for doc_file in request.FILES.getlist('documents[]'):
            MissionDocument.objects.create(house=house, file=doc_file, name=doc_file.name)
            
        # Process plans
        for plan_file in request.FILES.getlist('plans[]'):
            house.floor_plan_image = plan_file
            house.save()
            
        # Process medias
        for media_file in request.FILES.getlist('medias[]'):
            Room.objects.create(house=house, image=media_file, title=media_file.name.split('.')[0])
            
        # If the request indicates they want to stay on the page (e.g., via a query param)
        if request.POST.get('action') == 'save_and_stay':
            # We pass a flag to tell the template to stay on the same tab
            # But the redirect will lose the tab state unless we pass it. We can rely on javascript redirect.
            return JsonResponse({'status': 'success', 'house_id': house.id})
            
        return redirect('house_detail', house_id=house.id)
        
    return render(request, 'create_house.html', {'house': house})

@login_required
def house_detail(request, house_id):
    """View and manage a specific house/mission"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    rooms = house.rooms.all()
    parties = house.parties.all()
    documents = house.documents.all()
    medias = house.medias.all()
    return render(request, 'house_detail.html', {
        'house': house,
        'rooms': rooms,
        'parties': parties,
        'documents': documents,
        'medias': medias,
    })

@login_required
def delete_house(request, house_id):
    """Delete a house/mission"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    if request.method == 'POST':
        house.delete()
        from django.contrib import messages
        messages.success(request, 'Mission supprimée avec succès.')
        return redirect('house_list')
    # If not POST, just redirect back to list
    return redirect('house_list')

@login_required
def add_room(request, house_id):
    """Add a new 360° room image to a house"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.house = house
            
            # If this is marked as starting point, unmark others
            if room.is_starting_point:
                house.rooms.update(is_starting_point=False)
            
            room.save()
            return redirect('house_detail', house_id=house.id)
    else:
        form = RoomForm()
    return render(request, 'add_room.html', {'form': form, 'house': house})

@login_required
def edit_room_position(request, room_id):
    """Edit room position on floor plan"""
    room = get_object_or_404(Room, id=room_id, house__owner=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        room.floor_plan_x = data.get('x')
        room.floor_plan_y = data.get('y')
        room.save()
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_connection(request, room_id):
    """Add a hotspot connection from one room to another"""
    from_room = get_object_or_404(Room, id=room_id, house__owner=request.user)
    # Exclude the room itself AND rooms that already have a connection FROM this room
    connected_room_ids = from_room.connections_from.values_list('to_room_id', flat=True)
    available_rooms = from_room.house.rooms.exclude(id=room_id).exclude(id__in=connected_room_ids)
    
    if request.method == 'POST':
        form = RoomConnectionForm(request.POST)
        form.fields['to_room'].queryset = available_rooms
        if form.is_valid():
            connection = form.save(commit=False)
            connection.from_room = from_room
            try:
                connection.save()
                return redirect('house_detail', house_id=from_room.house.id)
            except IntegrityError:
                form.add_error('to_room', 'Une connexion vers cette pièce existe déjà.')
    else:
        form = RoomConnectionForm()
        form.fields['to_room'].queryset = available_rooms
    
    return render(request, 'add_connection.html', {
        'form': form,
        'room': from_room,
        'available_rooms': available_rooms
    })

@login_required
def delete_room(request, room_id):
    """Delete a room"""
    room = get_object_or_404(Room, id=room_id, house__owner=request.user)
    house_id = room.house.id
    room.delete()
    return redirect('house_detail', house_id=house_id)

@login_required
def add_media(request, house_id):
    """Upload non-360 media files (images, videos, audio) to a mission"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    if request.method == 'POST':
        files = request.FILES.getlist('media_files')
        for f in files:
            # Auto-detect media type from extension
            ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext in ('mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'):
                media_type = 'video'
            elif ext in ('mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'):
                media_type = 'audio'
            else:
                media_type = 'image'
            MissionMedia.objects.create(
                house=house,
                file=f,
                name=f.name,
                media_type=media_type
            )
        return redirect('house_detail', house_id=house.id)
    return redirect('house_detail', house_id=house.id)

@login_required
def delete_media(request, media_id):
    """Delete a non-360 media file"""
    media = get_object_or_404(MissionMedia, id=media_id, house__owner=request.user)
    house_id = media.house.id
    if request.method == 'POST':
        media.delete()
    return redirect('house_detail', house_id=house_id)

@login_required
def house_walkthrough(request, house_id):
    """Main walkthrough viewer with Pannellum"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    rooms = house.rooms.all()
    
    # Get starting room (or first room if none marked)
    starting_room = house.rooms.filter(is_starting_point=True).first()
    if not starting_room:
        starting_room = house.rooms.first()
    
    # Build scenes configuration for Pannellum
    scenes = {}
    for room in rooms:
        # Get all connections FROM this room
        connections = room.connections_from.all()
        hotspots = []
        
        for conn in connections:
            hotspots.append({
                'pitch': conn.pitch,
                'yaw': conn.yaw,
                'type': 'scene',
                'text': conn.label,
                'sceneId': f'room_{conn.to_room.id}'
            })
        
        scenes[f'room_{room.id}'] = {
            'title': room.title,
            'panorama': room.image.url,
            'hotSpots': hotspots
        }
    
    return render(request, 'house_walkthrough.html', {
        'house': house,
        'rooms': rooms,
        'starting_room': starting_room,
        'scenes_json': json.dumps(scenes),
        'default_scene': f'room_{starting_room.id}' if starting_room else None
    })

def public_walkthrough(request, share_token):
    """Public walkthrough viewer using share token (no login required)"""
    house = get_object_or_404(House, share_token=share_token)
    rooms = house.rooms.all()
    
    # Get starting room (or first room if none marked)
    starting_room = house.rooms.filter(is_starting_point=True).first()
    if not starting_room:
        starting_room = house.rooms.first()
    
    # Build scenes configuration for Pannellum
    scenes = {}
    for room in rooms:
        connections = room.connections_from.all()
        hotspots = []
        for conn in connections:
            hotspots.append({
                'pitch': conn.pitch,
                'yaw': conn.yaw,
                'type': 'scene',
                'text': conn.label,
                'sceneId': f'room_{conn.to_room.id}'
            })
        scenes[f'room_{room.id}'] = {
            'title': room.title,
            'panorama': room.image.url,
            'hotSpots': hotspots
        }
        
    return render(request, 'public_walkthrough.html', {
        'house': house,
        'rooms': rooms,
        'starting_room': starting_room,
        'scenes_json': json.dumps(scenes),
        'default_scene': f'room_{starting_room.id}' if starting_room else None
    })