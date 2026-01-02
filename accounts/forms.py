from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    gaming_id = forms.CharField(max_length=50, required=False)
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 
                  'phone', 'gaming_id', 'profile_picture']

class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = ['email', 'phone', 'gaming_id', 'profile_picture']