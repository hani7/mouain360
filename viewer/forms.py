from django import forms
from .models import Image, House, Room, RoomConnection, RoomPoint

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['title', 'image']

class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'description', 'floor_plan_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Entrez la description de la maison...'}),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['title', 'image', 'is_starting_point']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ex: Salon, Cuisine, Chambre'}),
        }

class RoomConnectionForm(forms.ModelForm):
    class Meta:
        model = RoomConnection
        fields = ['to_room', 'pitch', 'yaw', 'label']
        widgets = {
            'pitch': forms.HiddenInput(),
            'yaw': forms.HiddenInput(),
            'label': forms.TextInput(attrs={'placeholder': 'Ex: Aller à la Cuisine'}),
        }

class RoomPointForm(forms.ModelForm):
    class Meta:
        model = RoomPoint
        fields = ['pitch', 'yaw', 'kind', 'description', 'file']
        widgets = {
            'pitch': forms.HiddenInput(),
            'yaw': forms.HiddenInput(),
            'description': forms.TextInput(attrs={'placeholder': 'Ex: Vidéo de la cuisine, Prise électrique...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data.get('kind')
        if kind and kind != 'info' and not cleaned_data.get('file'):
            self.add_error('file', 'Veuillez ajouter un fichier pour ce type de point.')
        return cleaned_data
