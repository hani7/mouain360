from django.contrib import admin
from .models import Image, House, Room, RoomConnection

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_at']
    search_fields = ['title']

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'house', 'is_starting_point', 'uploaded_at']
    list_filter = ['house', 'is_starting_point']
    search_fields = ['title', 'house__name']

@admin.register(RoomConnection)
class RoomConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_room', 'to_room', 'label']
    list_filter = ['from_room__house']
    search_fields = ['from_room__title', 'to_room__title', 'label']
