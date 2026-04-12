from django.urls import path, include
from . import views

app_name = 'home_tour'

# Public URLs (accessible to everyone)
public_patterns = [
    # Home listing and viewing
    path('', views.home_list, name='home_list'),
    path('homes/<int:home_id>/', views.home_detail, name='home_detail'),
    
    # Room 360 viewing
    path('rooms/<int:room_id>/360/', views.room_360_view, name='room_360_view'),
    
    # Tour viewing
    path('tours/<int:tour_id>/', views.tour_view, name='tour_view'),
    
    # QR Code generation
    path('homes/<int:home_id>/qr/', views.generate_home_qr, name='generate_home_qr'),
]

# Dashboard URLs (require authentication)
dashboard_patterns = [
    # Home management
    path('', views.my_homes, name='my_homes'),
    path('create/', views.create_home, name='create_home'),
    path('<int:home_id>/', views.home_dashboard, name='home_dashboard'),
    path('<int:home_id>/edit/', views.edit_home, name='edit_home'),
    path('<int:home_id>/delete/', views.delete_home, name='delete_home'),
    
    # Room management
    path('<int:home_id>/rooms/add/', views.add_room, name='add_room'),
    path('rooms/<int:room_id>/edit/', views.edit_room, name='edit_room'),
    path('rooms/<int:room_id>/delete/', views.delete_room, name='delete_room'),
    path('rooms/<int:room_id>/editor/', views.room_editor, name='room_editor'),
    
    # Hotspot management
    path('hotspots/save/', views.save_hotspot, name='save_hotspot'),
    path('hotspots/<int:hotspot_id>/delete/', views.delete_hotspot, name='delete_hotspot'),
    path('hotspots/<int:hotspot_id>/edit/', views.edit_hotspot, name='edit_hotspot'),
    path('hotspots/bulk-action/', views.bulk_hotspot_action, name='bulk_hotspot_action'),
    
    # Hotspot media management
    path('hotspots/<int:hotspot_id>/media/add/', views.add_hotspot_media, name='add_hotspot_media'),
    path('media/<int:media_id>/delete/', views.delete_hotspot_media, name='delete_hotspot_media'),
    
    # Tour management
    path('<int:home_id>/tours/create/', views.create_tour, name='create_tour'),
    path('tours/<int:tour_id>/edit/', views.edit_tour, name='edit_tour'),
    path('tours/<int:tour_id>/delete/', views.delete_tour, name='delete_tour'),
    path('tours/<int:tour_id>/editor/', views.tour_editor, name='tour_editor'),
    
    # Tour step management
    path('tours/<int:tour_id>/steps/add/', views.add_tour_step, name='add_tour_step'),
    path('steps/<int:step_id>/edit/', views.edit_tour_step, name='edit_tour_step'),
    path('steps/<int:step_id>/delete/', views.delete_tour_step, name='delete_tour_step'),
    path('steps/reorder/', views.reorder_tour_steps, name='reorder_tour_steps'),
    
    # Analytics
    path('<int:home_id>/analytics/', views.home_analytics, name='home_analytics'),
    path('<int:home_id>/analytics/export/', views.export_analytics, name='export_analytics'),
]

# API URLs (for AJAX requests)
api_patterns = [
    # Room data
    path('rooms/<int:room_id>/data/', views.room_data_api, name='room_data_api'),
    path('rooms/<int:room_id>/hotspots/', views.room_hotspots_api, name='room_hotspots_api'),
    
    # Tour data
    path('tours/<int:tour_id>/data/', views.tour_data_api, name='tour_data_api'),
    
    # Analytics data
    path('homes/<int:home_id>/visits/', views.home_visits_api, name='home_visits_api'),
    
    # Image upload
    path('upload/360-image/', views.upload_360_image_api, name='upload_360_image_api'),
    
    # Hotspot positioning
    path('hotspots/position/', views.save_hotspot_position, name='save_hotspot_position'),
]

urlpatterns = [
    # Include all patterns
    path('', include(public_patterns)),
    path('dashboard/', include(dashboard_patterns)),
    path('api/', include(api_patterns)),
]