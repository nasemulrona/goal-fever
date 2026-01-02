from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm
from .models import User, PlayerProfile

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # PlayerProfile তৈরি করার আগে চেক করুন যে ইতিমধ্যে তৈরি হয়েছে কিনা
            if not hasattr(user, 'playerprofile'):
                PlayerProfile.objects.create(user=user)
            
            # Auto login after registration
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Goal Fever!")
            return redirect('home')
        else:
            # Form errors দেখান
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('home')

@login_required
def profile_view(request):
    """User profile view"""
    if request.user.is_admin:
        messages.warning(request, "Admins don't have player profiles.")
        return redirect('home')
    
    # PlayerProfile তৈরি করুন যদি না থাকে
    player_profile, created = PlayerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'player_profile': player_profile,
    }
    return render(request, 'accounts/profile.html', context)