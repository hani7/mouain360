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
            'label': 'Description de la pièce jointe',
            'file': 'Sélectionner le fichier',
        }
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': "Ex: Plan d'étage PDF, Dessin technique, etc.", 'required': True}),
            'file': forms.FileInput(attrs={'accept': '*/*', 'required': True}),
        }

class HotspotForm(forms.ModelForm):
    class Meta:
        model = Hotspot
        fields = ['x_percent', 'y_percent', 'target_image', 'label']