from django.db import models

class FloorPlan(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='floor_plans/')
    created_at = models.DateTimeField(auto_now_add=True)

class FloorPlanAttachment(models.Model):
    floor_plan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE, related_name='attachments')
    label = models.CharField(max_length=255)
    file = models.FileField(upload_to='floor_plan_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.label} - {self.floor_plan.title}"

class Hotspot(models.Model):
    floor_plan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE, related_name='hotspots')
    x_percent = models.FloatField()  # x position as % of image width
    y_percent = models.FloatField()  # y position as % of image height
    target_image = models.ImageField(upload_to='hotspot_targets/', blank=True, null=True)
    label = models.CharField(max_length=255, blank=True)
