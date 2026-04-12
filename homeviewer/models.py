from django.db import models
from django.contrib.auth.models import User
import json

class Home(models.Model):
    """Model for a home/property"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to='home_thumbnails/', blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    def get_starting_room(self):
        """Get the first room to start the tour"""
        return self.rooms.filter(is_starting_room=True).first() or self.rooms.first()

class Room(models.Model):
    """Model for rooms in a home"""
    ROOM_TYPES = [
        ('living_room', 'Living Room'),
        ('bedroom', 'Bedroom'),
        ('kitchen', 'Kitchen'),
        ('bathroom', 'Bathroom'),
        ('dining_room', 'Dining Room'),
        ('office', 'Office'),
        ('garage', 'Garage'),
        ('outdoor', 'Outdoor'),
        ('other', 'Other'),
    ]
    
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='other')
    image_360 = models.ImageField(upload_to='360_images/')
    description = models.TextField(blank=True)
    is_starting_room = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.home.title} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one starting room per home
        if self.is_starting_room:
            Room.objects.filter(home=self.home, is_starting_room=True).update(is_starting_room=False)
        super().save(*args, **kwargs)

class Hotspot(models.Model):
    """Model for interactive hotspots in 360 images"""
    HOTSPOT_TYPES = [
        ('navigation', 'Navigation'),
        ('info', 'Information'),
        ('media', 'Media'),
        ('link', 'External Link'),
    ]
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='hotspots')
    name = models.CharField(max_length=100)
    hotspot_type = models.CharField(max_length=20, choices=HOTSPOT_TYPES, default='info')
    
    # 3D coordinates for hotspot placement (spherical coordinates)
    yaw = models.FloatField(help_text="Horizontal angle in degrees (-180 to 180)")
    pitch = models.FloatField(help_text="Vertical angle in degrees (-90 to 90)")
    
    # Content for different hotspot types
    description = models.TextField(blank=True)
    target_room = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                   help_text="Target room for navigation hotspots")
    external_url = models.URLField(blank=True, help_text="External URL for link hotspots")
    
    # Visual properties
    icon = models.CharField(max_length=50, default='info', 
                           help_text="CSS class or icon name")
    color = models.CharField(max_length=7, default='#ffffff', 
                            help_text="Hex color code")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.room.name} - {self.name}"

class HotspotMedia(models.Model):
    """Model for media attachments to hotspots"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    hotspot = models.ForeignKey(Hotspot, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='hotspot_media/')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.hotspot.name} - {self.title or self.media_type}"

class Tour(models.Model):
    """Model for guided tours through a home"""
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='tours')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.home.title} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default tour per home
        if self.is_default:
            Tour.objects.filter(home=self.home, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class TourStep(models.Model):
    """Model for individual steps in a tour"""
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='steps')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(default=10, 
                                          help_text="Duration in seconds")
    
    # Auto-rotation settings
    auto_rotate = models.BooleanField(default=True)
    rotation_speed = models.FloatField(default=1.0, 
                                      help_text="Rotation speed (0.1 to 5.0)")
    
    class Meta:
        ordering = ['order']
        unique_together = ['tour', 'order']
    
    def __str__(self):
        return f"{self.tour.name} - Step {self.order}: {self.room.name}"

class HomeVisit(models.Model):
    """Model to track home visits for analytics"""
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='visits')
    visitor_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    visit_duration = models.DurationField(null=True, blank=True)
    rooms_visited = models.JSONField(default=list)
    visited_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Visit to {self.home.title} on {self.visited_at}"