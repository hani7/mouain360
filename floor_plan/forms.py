from django import forms
from .models import FloorPlan, Hotspot, FloorPlanAttachment

class FloorPlanForm(forms.ModelForm):
    class Meta:
        model = FloorPlan
        fields = ['title', 'image']

class FloorPlanAttachmentForm(forms.ModelForm):
    class Meta:
        model = FloorPlanAttachment
        fields = ['label', 'file']
        labels = {
            'label': 'Attachment Label/Description',
            'file': 'Select File',
        }
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'e.g., Floor Plan PDF, Technical Drawing, etc.', 'required': True}),
            'file': forms.FileInput(attrs={'accept': '*/*', 'required': True}),
        }

class HotspotForm(forms.ModelForm):
    class Meta:
        model = Hotspot
        fields = ['x_percent', 'y_percent', 'target_image', 'label']