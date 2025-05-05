from django import forms
from django.contrib.auth.forms import UserCreationForm

class UserForm(UserCreationForm):
    pass

class VideoUploadForm(forms.Form):
    video = forms.FileField(label='Select a video', required=True)