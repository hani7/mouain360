from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Original image viewer URLs
    path('upload/', views.upload_image, name='upload_image'),
    path('view/', views.view_images, name='view_images'),
    path('view/<int:image_id>/', views.view_360_image, name='view_360_image'),
    path('delete/<int:image_id>/', views.delete_image, name='delete_image'),
    path('download_qr_code/<int:image_id>/', views.download_qr_code, name='download_qr_code'),
    
    # Public tour URL (no login required)
    path('tour/<uuid:share_token>/', views.public_walkthrough, name='public_tour'),
    
    # House walkthrough URLs
    path('houses/', views.house_list, name='house_list'),
    path('house/create/', views.create_house, name='create_house'),
    path('house/<int:house_id>/edit/', views.edit_house, name='edit_house'),
    path('house/<int:house_id>/', views.house_detail, name='house_detail'),
    path('house/<int:house_id>/delete/', views.delete_house, name='delete_house'),
    path('house/<int:house_id>/add-room/', views.add_room, name='add_room'),
    path('house/<int:house_id>/walkthrough/', views.house_walkthrough, name='house_walkthrough'),
    path('house/<int:house_id>/qr-code/', views.download_house_qr_code, name='download_house_qr_code'),
    path('room/<int:room_id>/edit-position/', views.edit_room_position, name='edit_room_position'),
    path('room/<int:room_id>/add-connection/', views.add_connection, name='add_connection'),
    path('room/<int:room_id>/delete/', views.delete_room, name='delete_room'),
    path('room/<int:room_id>/set-starting-point/', views.set_starting_point, name='set_starting_point'),
    path('house/<int:house_id>/add-media/', views.add_media, name='add_media'),
    path('media/<int:media_id>/delete/', views.delete_media, name='delete_media'),
]
