from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import json

from viewer.utils import generate_qr_code
from floor_plan.models import FloorPlan
from .models import Image, House, Room, RoomConnection
from .forms import ImageUploadForm, HouseForm, RoomForm, RoomConnectionForm

# ===== Dashboard View =====

@login_required
def dashboard(request):
    """Main dashboard showing user stats and recent activity."""
    # Metrics
    house_count = House.objects.filter(owner=request.user).count()
    room_count = Room.objects.filter(house__owner=request.user).count()
    floorplan_count = FloorPlan.objects.filter(owner=request.user).count()
    
    # Recent activity
    recent_houses = House.objects.filter(owner=request.user).order_by('-created_at')[:3]
    
    context = {
        'house_count': house_count,
        'room_count': room_count,
        'floorplan_count': floorplan_count,
        'recent_houses': recent_houses,
    }
    return render(request, 'dashboard.html', context)

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
    walkthrough_url = request.build_absolute_uri(f'/viewer/house/{house_id}/walkthrough/')
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
    """Create a new house"""
    if request.method == 'POST':
        form = HouseForm(request.POST, request.FILES)
        if form.is_valid():
            house = form.save(commit=False)
            house.owner = request.user
            house.save()
            return redirect('house_detail', house_id=house.id)
    else:
        form = HouseForm()
    return render(request, 'create_house.html', {'form': form})

@login_required
def house_detail(request, house_id):
    """Manage rooms and connections for a house"""
    house = get_object_or_404(House, id=house_id, owner=request.user)
    rooms = house.rooms.all()
    return render(request, 'house_detail.html', {
        'house': house,
        'rooms': rooms
    })

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
        'scenes_json': json.dumps(scenes)
    })