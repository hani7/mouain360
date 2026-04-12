from django.db import models

class Image(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='360_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class House(models.Model):
    """Represents a property/house with multiple 360° images"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    floor_plan_image = models.ImageField(upload_to='floor_plans/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

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
