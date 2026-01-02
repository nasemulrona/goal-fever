# tournaments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Tournament, TournamentRegistration, Team, Match, Schedule

# Add home_view to fix the import error
def home_view(request):
    """Home page view"""
    # You can add context or logic here
    context = {
        'message': 'Welcome to Goal Fever!',
    }
    return render(request, 'home.html', context)

@login_required
def tournament_register(request, tournament_id):
    """Register for a tournament"""
    tournament = get_object_or_404(Tournament, id=tournament_id, is_active=True)
    
    # Check if already registered
    if TournamentRegistration.objects.filter(player=request.user, tournament=tournament).exists():
        messages.warning(request, "You are already registered for this tournament!")
        return redirect('home')
    
    if request.method == 'POST':
        team_id = request.POST.get('team')
        team = get_object_or_404(Team, id=team_id)
        
        # Create registration
        registration = TournamentRegistration.objects.create(
            player=request.user,
            tournament=tournament,
            selected_team=team,
            is_paid=False
        )
        
        messages.success(request, f"Successfully registered for {tournament.name}!")
        return redirect('payment_process', registration_id=registration.id)
    
    # Get all teams
    teams = Team.objects.all().order_by('name')
    
    context = {
        'tournament': tournament,
        'teams': teams,
    }
    return render(request, 'tournaments/register.html', context)

@login_required
def team_selection(request, registration_id):
    """Team selection view"""
    registration = get_object_or_404(TournamentRegistration, id=registration_id, player=request.user)
    
    if request.method == 'POST':
        team_id = request.POST.get('team')
        team = get_object_or_404(Team, id=team_id)
        registration.selected_team = team
        registration.save()
        return redirect('payment_process', registration_id=registration.id)
    
    teams = Team.objects.all().order_by('name')
    
    context = {
        'registration': registration,
        'teams': teams,
    }
    return render(request, 'tournaments/team_selection.html', context)

def schedule_view(request):
    """View tournament schedule"""
    schedules = Schedule.objects.filter(is_published=True).select_related('tournament')
    
    context = {
        'schedules': schedules,
    }
    return render(request, 'tournaments/schedule.html', context)

@login_required
def my_matches(request):
    """View user's matches"""
    # Simple admin check using Django's built-in user attributes
    if request.user.is_superuser or request.user.is_staff:
        messages.warning(request, "Admins don't have matches.")
        return redirect('home')
    
    # Get matches for the user
    matches = Match.objects.filter(
        Q(player1=request.user) | Q(player2=request.user)
    ).select_related('tournament', 'player1', 'player2')
    
    context = {
        'matches': matches,
    }
    return render(request, 'tournaments/my_matches.html', context)

@login_required
def submit_screenshot(request, match_id):
    """Submit match screenshot"""
    match = get_object_or_404(Match, id=match_id)
    
    if match.player1 != request.user and match.player2 != request.user:
        messages.error(request, "You are not authorized to submit for this match!")
        return redirect('my_matches')
    
    if request.method == 'POST' and request.FILES.get('screenshot'):
        match.screenshot = request.FILES['screenshot']
        match.save()
        messages.success(request, "Screenshot submitted successfully!")
        return redirect('my_matches')
    
    context = {
        'match': match,
    }
    return render(request, 'tournaments/submit_screenshot.html', context)