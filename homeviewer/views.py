from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
import json
import logging

from .models import Home, Room, Hotspot, HotspotMedia, Tour, TourStep, HomeVisit
from .forms import HomeForm, RoomForm, HotspotForm, TourForm # type: ignore
from .utils import generate_qr_code # type: ignore

logger = logging.getLogger(__name__)

def home_list(request):
    """List all public homes"""
    homes = Home.objects.filter(is_public=True).order_by('-created_at')
    paginator = Paginator(homes, 12)  # Show 12 homes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_homes': homes.count()
    }
    return render(request, 'homes/home_list.html', context)

def home_detail(request, home_id):
    """View a specific home's details and rooms"""
    home = get_object_or_404(Home, id=home_id, is_public=True)
    rooms = home.rooms.all()
    tours = home.tours.all()
    default_tour = home.tours.filter(is_default=True).first()
    
    # Track visit
    _track_home_visit(request, home)
    
    context = {
        'home': home,
        'rooms': rooms,
        'tours': tours,
        'default_tour': default_tour,
        'starting_room': home.get_starting_room()
    }
    return render(request, 'homes/home_detail.html', context)

def room_360_view(request, room_id):
    """Display 360-degree view of a room with hotspots"""
    room = get_object_or_404(Room, id=room_id)
    
    # Check if home is public or user owns it
    if not room.home.is_public and room.home.owner != request.user:
        messages.error(request, "You don't have permission to view this room.")
        return redirect('home_list')
    
    hotspots = room.hotspots.filter(is_active=True)
    other_rooms = room.home.rooms.exclude(id=room.id)
    
    # Prepare hotspot data for JavaScript
    hotspot_data = []
    for hotspot in hotspots:
        data = {
            'id': hotspot.id,
            'name': hotspot.name,
            'type': hotspot.hotspot_type,
            'yaw': hotspot.yaw,
            'pitch': hotspot.pitch,
            'description': hotspot.description,
            'icon': hotspot.icon,
            'color': hotspot.color,
        }
        
        if hotspot.hotspot_type == 'navigation' and hotspot.target_room:
            data['target_room_id'] = hotspot.target_room.id
            data['target_room_name'] = hotspot.target_room.name
        elif hotspot.hotspot_type == 'link':
            data['external_url'] = hotspot.external_url
        elif hotspot.hotspot_type == 'media':
            data['media'] = [
                {
                    'type': media.media_type,
                    'url': media.file.url,
                    'title': media.title,
                    'description': media.description
                }
                for media in hotspot.media.all()
            ]
        
        hotspot_data.append(data)
    
    context = {
        'room': room,
        'home': room.home,
        'hotspots': hotspots,
        'hotspot_data': json.dumps(hotspot_data),
        'other_rooms': other_rooms
    }
    return render(request, 'rooms/room_360_view.html', context)

def tour_view(request, tour_id):
    """Display guided tour interface"""
    tour = get_object_or_404(Tour, id=tour_id)
    
    if not tour.home.is_public and tour.home.owner != request.user:
        messages.error(request, "You don't have permission to view this tour.")
        return redirect('home_list')
    
    steps = tour.steps.all()
    
    # Prepare tour data for JavaScript
    tour_data = {
        'id': tour.id,
        'name': tour.name,
        'description': tour.description,
        'steps': [
            {
                'order': step.order,
                'room_id': step.room.id,
                'room_name': step.room.name,
                'room_image': step.room.image_360.url,
                'title': step.title,
                'description': step.description,
                'duration': step.duration,
                'auto_rotate': step.auto_rotate,
                'rotation_speed': step.rotation_speed,
                'hotspots': [
                    {
                        'id': hotspot.id,
                        'name': hotspot.name,
                        'type': hotspot.hotspot_type,
                        'yaw': hotspot.yaw,
                        'pitch': hotspot.pitch,
                        'description': hotspot.description,
                        'icon': hotspot.icon,
                        'color': hotspot.color,
                    }
                    for hotspot in step.room.hotspots.filter(is_active=True)
                ]
            }
            for step in steps
        ]
    }
    
    context = {
        'tour': tour,
        'home': tour.home,
        'steps': steps,
        'tour_data': json.dumps(tour_data)
    }
    return render(request, 'tours/tour_view.html', context)

@login_required
def my_homes(request):
    """List homes owned by the current user"""
    homes = Home.objects.filter(owner=request.user).order_by('-created_at')
    
    context = {
        'homes': homes
    }
    return render(request, 'dashboard/my_homes.html', context)

@login_required
def create_home(request):
    """Create a new home"""
    if request.method == 'POST':
        form = HomeForm(request.POST, request.FILES)
        if form.is_valid():
            home = form.save(commit=False)
            home.owner = request.user
            home.save()
            messages.success(request, 'Home created successfully!')
            return redirect('home_dashboard', home_id=home.id)
    else:
        form = HomeForm()
    
    return render(request, 'dashboard/create_home.html', {'form': form})

@login_required
def home_dashboard(request, home_id):
    """Dashboard for managing a specific home"""
    home = get_object_or_404(Home, id=home_id, owner=request.user)
    rooms = home.rooms.all()
    tours = home.tours.all()
    
    # Get recent visits
    recent_visits = home.visits.order_by('-visited_at')[:10]
    
    context = {
        'home': home,
        'rooms': rooms,
        'tours': tours,
        'recent_visits': recent_visits,
        'total_visits': home.visits.count()
    }
    return render(request, 'dashboard/home_dashboard.html', context)

@login_required
def add_room(request, home_id):
    """Add a new room to a home"""
    home = get_object_or_404(Home, id=home_id, owner=request.user)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.home = home
            room.save()
            messages.success(request, f'Room "{room.name}" added successfully!')
            return redirect('room_editor', room_id=room.id)
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'home': home
    }
    return render(request, 'dashboard/add_room.html', context)

@login_required
def room_editor(request, room_id):
    """Editor for managing room hotspots"""
    room = get_object_or_404(Room, id=room_id, home__owner=request.user)
    hotspots = room.hotspots.all()
    
    context = {
        'room': room,
        'home': room.home,
        'hotspots': hotspots,
        'room_choices': room.home.rooms.exclude(id=room.id)
    }
    return render(request, 'dashboard/room_editor.html', context)

@login_required
@csrf_exempt
def save_hotspot(request):
    """AJAX endpoint to save hotspot data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        room = get_object_or_404(Room, id=room_id, home__owner=request.user)
        
        hotspot_id = data.get('hotspot_id')
        if hotspot_id:
            # Update existing hotspot
            hotspot = get_object_or_404(Hotspot, id=hotspot_id, room=room)
        else:
            # Create new hotspot
            hotspot = Hotspot(room=room)
        
        # Update hotspot data
        hotspot.name = data.get('name', 'Unnamed Hotspot')
        hotspot.hotspot_type = data.get('type', 'info')
        hotspot.yaw = float(data.get('yaw', 0))
        hotspot.pitch = float(data.get('pitch', 0))
        hotspot.description = data.get('description', '')
        hotspot.icon = data.get('icon', 'info')
        hotspot.color = data.get('color', '#ffffff')
        
        if hotspot.hotspot_type == 'navigation':
            target_room_id = data.get('target_room_id')
            if target_room_id:
                hotspot.target_room = get_object_or_404(Room, id=target_room_id, home=room.home)
        elif hotspot.hotspot_type == 'link':
            hotspot.external_url = data.get('external_url', '')
        
        hotspot.save()
        
        return JsonResponse({
            'success': True,
            'hotspot_id': hotspot.id,
            'message': 'Hotspot saved successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error saving hotspot: {str(e)}")
        return JsonResponse({
            'error': 'Failed to save hotspot',
            'details': str(e)
        }, status=400)

@login_required
def delete_hotspot(request, hotspot_id):
    """Delete a hotspot"""
    hotspot = get_object_or_404(Hotspot, id=hotspot_id, room__home__owner=request.user)
    room = hotspot.room
    
    if request.method == 'POST':
        hotspot.delete()
        messages.success(request, 'Hotspot deleted successfully!')
        return redirect('room_editor', room_id=room.id)
    
    context = {
        'hotspot': hotspot,
        'room': room
    }
    return render(request, 'dashboard/confirm_delete_hotspot.html', context)

@login_required
def create_tour(request, home_id):
    """Create a new tour for a home"""
    home = get_object_or_404(Home, id=home_id, owner=request.user)
    
    if request.method == 'POST':
        form = TourForm(request.POST)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.home = home
            tour.save()
            messages.success(request, 'Tour created successfully!')
            return redirect('tour_editor', tour_id=tour.id)
    else:
        form = TourForm()
    
    context = {
        'form': form,
        'home': home
    }
    return render(request, 'dashboard/create_tour.html', context)

@login_required
def tour_editor(request, tour_id):
    """Editor for managing tour steps"""
    tour = get_object_or_404(Tour, id=tour_id, home__owner=request.user)
    steps = tour.steps.all()
    available_rooms = tour.home.rooms.all()
    
    context = {
        'tour': tour,
        'home': tour.home,
        'steps': steps,
        'available_rooms': available_rooms
    }
    return render(request, 'dashboard/tour_editor.html', context)

def generate_home_qr(request, home_id):
    """Generate QR code for home URL"""
    home = get_object_or_404(Home, id=home_id, is_public=True)
    home_url = request.build_absolute_uri(f'/homes/{home.id}/')
    
    qr_code = generate_qr_code(home_url)
    
    response = HttpResponse(qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_code_home_{home.id}.png"'
    
    return response

def _track_home_visit(request, home):
    """Helper function to track home visits"""
    try:
        visitor_ip = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create visit record
        HomeVisit.objects.create(
            home=home,
            visitor_ip=visitor_ip,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error tracking home visit: {str(e)}")

def _get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip