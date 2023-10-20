from django import forms
from .models import ImageModel
from .models import VideoModel

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = VideoModel
        fields = ['video']

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageModel
        fields = ['image']