from django import forms
from django.core.exceptions import ValidationError
from .models import Home, Room, Hotspot, HotspotMedia, Tour, TourStep

class HomeForm(forms.ModelForm):
    """Form for creating and editing homes"""
    
    class Meta:
        model = Home
        fields = ['title', 'description', 'address', 'is_public', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter home title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your home...'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter full address (optional)'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            # Check file size (max 5MB)
            if thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError("Thumbnail file size cannot exceed 5MB.")
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if not any(thumbnail.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError("Thumbnail must be a JPEG, PNG, or WebP image.")
        
        return thumbnail

class RoomForm(forms.ModelForm):
    """Form for creating and editing rooms"""
    
    class Meta:
        model = Room
        fields = ['name', 'room_type', 'image_360', 'description', 'is_starting_room', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter room name'
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image_360': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this room...'
            }),
            'is_starting_room': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
    
    def clean_image_360(self):
        image = self.cleaned_data.get('image_360')
        if image:
            # Check file size (max 20MB for 360 images)
            if image.size > 20 * 1024 * 1024:
                raise ValidationError("360° image file size cannot exceed 20MB.")
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError("360° image must be a JPEG or PNG file.")
        
        return image
    
    def clean_order(self):
        order = self.cleaned_data.get('order')
        if order is not None and order < 0:
            raise ValidationError("Order must be a positive number.")
        return order

class HotspotForm(forms.ModelForm):
    """Form for creating and editing hotspots"""
    
    class Meta:
        model = Hotspot
        fields = [
            'name', 'hotspot_type', 'yaw', 'pitch', 'description', 
            'target_room', 'external_url', 'icon', 'color', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter hotspot name'
            }),
            'hotspot_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'yaw': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '-180',
                'max': '180',
                'step': '0.1'
            }),
            'pitch': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '-90',
                'max': '90',
                'step': '0.1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this hotspot...'
            }),
            'target_room': forms.Select(attrs={
                'class': 'form-select'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., info, arrow, camera'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)
        
        if room:
            # Filter target_room choices to rooms in the same home
            self.fields['target_room'].queryset = Room.objects.filter(
                home=room.home
            ).exclude(id=room.id)
        else:
            self.fields['target_room'].queryset = Room.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        hotspot_type = cleaned_data.get('hotspot_type')
        target_room = cleaned_data.get('target_room')
        external_url = cleaned_data.get('external_url')
        
        # Validate based on hotspot type
        if hotspot_type == 'navigation' and not target_room:
            self.add_error('target_room', 'Target room is required for navigation hotspots.')
        
        if hotspot_type == 'link' and not external_url:
            self.add_error('external_url', 'External URL is required for link hotspots.')
        
        return cleaned_data
    
    def clean_yaw(self):
        yaw = self.cleaned_data.get('yaw')
        if yaw is not None and (yaw < -180 or yaw > 180):
            raise ValidationError("Yaw must be between -180 and 180 degrees.")
        return yaw
    
    def clean_pitch(self):
        pitch = self.cleaned_data.get('pitch')
        if pitch is not None and (pitch < -90 or pitch > 90):
            raise ValidationError("Pitch must be between -90 and 90 degrees.")
        return pitch

class HotspotMediaForm(forms.ModelForm):
    """Form for adding media to hotspots"""
    
    class Meta:
        model = HotspotMedia
        fields = ['media_type', 'file', 'title', 'description', 'order']
        widgets = {
            'media_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter media title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe this media...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        media_type = self.cleaned_data.get('media_type')
        
        if file and media_type:
            # File size limits based on media type
            size_limits = {
                'image': 10 * 1024 * 1024,  # 10MB
                'video': 100 * 1024 * 1024,  # 100MB
                'audio': 20 * 1024 * 1024,   # 20MB
            }
            
            max_size = size_limits.get(media_type, 10 * 1024 * 1024)
            if file.size > max_size:
                raise ValidationError(f"{media_type.title()} file size cannot exceed {max_size // (1024*1024)}MB.")
            
            # File extension validation
            valid_extensions = {
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'video': ['.mp4', '.webm', '.ogg', '.mov'],
                'audio': ['.mp3', '.wav', '.ogg', '.m4a']
            }
            
            allowed_exts = valid_extensions.get(media_type, [])
            if not any(file.name.lower().endswith(ext) for ext in allowed_exts):
                raise ValidationError(f"Invalid file type for {media_type}. Allowed: {', '.join(allowed_exts)}")
        
        return file

class TourForm(forms.ModelForm):
    """Form for creating and editing tours"""
    
    class Meta:
        model = Tour
        fields = ['name', 'description', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tour name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this tour...'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class TourStepForm(forms.ModelForm):
    """Form for creating and editing tour steps"""
    
    class Meta:
        model = TourStep
        fields = [
            'room', 'order', 'title', 'description', 'duration', 
            'auto_rotate', 'rotation_speed'
        ]
        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-select'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter step title (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this step...'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'max': '300'
            }),
            'auto_rotate': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'rotation_speed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '5.0',
                'step': '0.1'
            })
        }
    
    def __init__(self, *args, **kwargs):
        tour = kwargs.pop('tour', None)
        super().__init__(*args, **kwargs)
        
        if tour:
            # Filter room choices to rooms in the tour's home
            self.fields['room'].queryset = Room.objects.filter(home=tour.home)
        else:
            self.fields['room'].queryset = Room.objects.none()
    
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration is not None and (duration < 5 or duration > 300):
            raise ValidationError("Duration must be between 5 and 300 seconds.")
        return duration
    
    def clean_rotation_speed(self):
        speed = self.cleaned_data.get('rotation_speed')
        if speed is not None and (speed < 0.1 or speed > 5.0):
            raise ValidationError("Rotation speed must be between 0.1 and 5.0.")
        return speed

class BulkHotspotForm(forms.Form):
    """Form for bulk operations on hotspots"""
    
    ACTION_CHOICES = [
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('delete', 'Delete Selected'),
        ('change_color', 'Change Color'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    hotspot_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    # Optional fields for specific actions
    new_color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )
    
    def clean_hotspot_ids(self):
        ids_str = self.cleaned_data.get('hotspot_ids')
        if not ids_str:
            raise ValidationError("No hotspots selected.")
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
            if not ids:
                raise ValidationError("No valid hotspot IDs provided.")
            return ids
        except ValueError:
            raise ValidationError("Invalid hotspot IDs provided.")
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_color = cleaned_data.get('new_color')
        
        if action == 'change_color' and not new_color:
            self.add_error('new_color', 'Color is required for color change action.')
        
        return cleaned_data