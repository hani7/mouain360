from django.db import models
from django.contrib.auth.models import User
import uuid

class Image(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standalone_images', null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='360_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class House(models.Model):
    """Represents a property/house with multiple 360° images"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='houses', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    floor_plan_image = models.ImageField(upload_to='floor_plans/', blank=True, null=True)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New dashboard fields
    reference = models.CharField(max_length=50, blank=True, null=True)
    mission_type = models.CharField(max_length=100, default='Visite 360')
    STATUS_CHOICES = [
        ('En cours', 'En cours'),
        ('Achevé', 'Achevé'),
        ('En retard', 'En retard'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='En cours')
    deadline = models.DateField(null=True, blank=True)

    # Nouvelle Mission Fields
    official_title = models.CharField(max_length=255, blank=True)
    order_date = models.DateField(null=True, blank=True)
    reception_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    client = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=255, blank=True)
    wilaya = models.CharField(max_length=100, blank=True)
    commune = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class MissionParty(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='parties')
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100) # e.g., 'Demandeur', 'Entreprise', 'Autre'

    def __str__(self):
        return f"{self.name} ({self.role})"

class MissionDocument(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='mission_documents/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class MissionMedia(models.Model):
    """Non-360 media files: videos, sounds, regular images"""
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
    ]
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='medias')
    file = models.FileField(upload_to='mission_medias/')
    name = models.CharField(max_length=255)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_media_type_display()})"

    @property
    def is_image(self):
        return self.media_type == 'image'

    @property
    def is_video(self):
        return self.media_type == 'video'

    @property
    def is_audio(self):
        return self.media_type == 'audio'

class Room(models.Model):
    """A single 360° image representing a room/location in a house"""
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='rooms')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='360_images/')
    is_starting_point = models.BooleanField(default=False, help_text="Is this the first room shown in walkthrough?")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Floor plan hotspot position (optional)
    floor_plan_x = models.FloatField(blank=True, null=True, help_text="X position % on floor plan")
    floor_plan_y = models.FloatField(blank=True, null=True, help_text="Y position % on floor plan")

    def __str__(self):
        return f"{self.house.name} - {self.title}"

    def save(self, *args, **kwargs):
        # We need to save the model first so we have the image file on disk
        super().save(*args, **kwargs)
        
        if self.image:
            try:
                from PIL import Image
                import os
                
                img_path = self.image.path
                img = Image.open(img_path)
                
                # Check if it needs resizing or format conversion
                # 360 images should ideally be max 4096x2048 for web performance
                max_width = 4096
                max_height = 2048
                
                if img.width > max_width or img.height > max_height or img.format != 'JPEG':
                    # Resize while maintaining aspect ratio (though 360 should be 2:1)
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if it's RGBA (PNG)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                        
                    # Save with compression
                    img.save(img_path, format='JPEG', quality=85, optimize=True)
            except Exception as e:
                # If Pillow is missing or there's an error, just skip compression
                print(f"Image compression failed: {e}")

    class Meta:
        ordering = ['house', 'title']

class RoomConnection(models.Model):
    """Hotspot that links one room to another in the 360° view"""
    from_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='connections_from')
    to_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='connections_to')
    pitch = models.FloatField(help_text="Vertical angle for hotspot in 360° view")
    yaw = models.FloatField(help_text="Horizontal angle for hotspot in 360° view")
    label = models.CharField(max_length=100, default='Go to room')

    def __str__(self):
        return f"{self.from_room.title} → {self.to_room.title}"

    class Meta:
        unique_together = ['from_room', 'to_room']
