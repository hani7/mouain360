from django.contrib import admin
from .models import FloorPlan, Hotspot, FloorPlanAttachment

@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title']

@admin.register(FloorPlanAttachment)
class FloorPlanAttachmentAdmin(admin.ModelAdmin):
    list_display = ['label', 'floor_plan', 'uploaded_at']
    list_filter = ['uploaded_at', 'floor_plan']
    search_fields = ['label', 'floor_plan__title']

@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ['label', 'floor_plan', 'x_percent', 'y_percent']
    list_filter = ['floor_plan']
    search_fields = ['label', 'floor_plan__title']
