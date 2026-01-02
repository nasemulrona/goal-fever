# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tournaments.models import Tournament, TournamentRegistration, Schedule, Team, Match
from accounts.models import PlayerProfile, User
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    """Home page view"""
    # Get active tournament
    active_tournament = Tournament.objects.filter(is_active=True, status='upcoming').first()
    
    # Create default tournament if not exists
    if not active_tournament:
        active_tournament = Tournament.objects.create(
            name="WORLD CUP 2026",
            description="International Football Tournament 2026",
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=60),
            registration_deadline=timezone.now() + timezone.timedelta(days=15),
            max_teams=32,
            entry_fee=150.00,
            status='upcoming',
            is_active=True
        )
    
    # Get user's registration status
    user_registration = None
    if request.user.is_authenticated and not request.user.is_admin and active_tournament:
        user_registration = TournamentRegistration.objects.filter(
            player=request.user, 
            tournament=active_tournament
        ).first()
    
    # Check if user is registered and payment confirmed for active tournament
    user_registered = False
    if request.user.is_authenticated and not request.user.is_admin and active_tournament:
        user_registered = TournamentRegistration.objects.filter(
            player=request.user, 
            tournament=active_tournament,
            payment_confirmed=True
        ).exists()
    
    # Rankings for players only (exclude admins)
    top_players = []
    if request.user.is_authenticated and not request.user.is_admin:
        top_players = PlayerProfile.objects.filter(
            user__is_admin=False,
            user__is_superuser=False
        ).select_related('user').order_by(
            '-matches_won',
            '-total_goals',
            '-ranking'
        )[:10]
        
        for player in top_players:
            player.total_points = (player.matches_won * 10) + player.total_goals
    
    # Recent registrations and schedules for logged in users
    recent_registrations = []
    schedules = []
    total_registrations = 0
    
    if request.user.is_authenticated:
        recent_registrations = TournamentRegistration.objects.filter(
            payment_confirmed=True
        ).select_related('player', 'selected_team').order_by('-registration_date')[:10]
        
        total_registrations = TournamentRegistration.objects.filter(
            payment_confirmed=True
        ).count()
        
        schedules = Schedule.objects.filter(is_published=True)[:5]
    
    # Get teams for display
    teams = Team.objects.all().order_by('name')[:32]
    
    # Get match stats
    live_matches = Match.objects.filter(status='ongoing').count()
    completed_matches = Match.objects.filter(status='completed').count()
    upcoming_matches = Match.objects.filter(status='scheduled').count()
    
    context = {
        'active_tournament': active_tournament,
        'user_registered': user_registered,
        'user_registration': user_registration,
        'top_players': top_players,
        'recent_registrations': recent_registrations,
        'schedules': schedules,
        'teams': teams,
        'total_registrations': total_registrations,
        'live_matches': live_matches,
        'completed_matches': completed_matches,
        'upcoming_matches': upcoming_matches,
    }
    
    return render(request, 'core/home.html', context)


# -----------------------------------------------------
# Tournament Register
# -----------------------------------------------------
@login_required
def tournament_register(request, tournament_id):
    """Tournament registration with team selection"""
    if request.user.is_admin or request.user.is_superuser:
        messages.warning(request, "Admins cannot register for tournaments.")
        return redirect('home')
    
    tournament = get_object_or_404(Tournament, id=tournament_id, is_active=True)
    
    # Check registration deadline
    if tournament.registration_deadline < timezone.now():
        messages.error(request, "Registration deadline has passed!")
        return redirect('home')
    
    # Check if already registered and payment confirmed
    existing_reg = TournamentRegistration.objects.filter(
        player=request.user, 
        tournament=tournament,
        payment_confirmed=True
    ).first()
    
    if existing_reg:
        messages.info(request, "You are already registered and payment confirmed!")
        return redirect('home')
    
    # Check if pending registration exists
    pending_reg = TournamentRegistration.objects.filter(
        player=request.user, 
        tournament=tournament,
        payment_confirmed=False
    ).first()
    
    if pending_reg:
        messages.info(request, "You have a pending registration. Please complete payment.")
        return redirect('payment_page', registration_id=pending_reg.id)
    
    if request.method == 'POST':
        team_id = request.POST.get('team')
        if not team_id:
            messages.error(request, "Please select a team!")
            return redirect('tournament_register', tournament_id=tournament_id)
        
        team = get_object_or_404(Team, id=team_id)
        
        # ✅ IMPORTANT: Check if team is already CONFIRMED in this tournament
        team_confirmed_taken = TournamentRegistration.objects.filter(
            tournament=tournament,
            selected_team=team,
            payment_confirmed=True
        ).exists()
        
        if team_confirmed_taken:
            messages.error(request, f"⚠️ Team '{team.name}' is already taken by another player!")
            return redirect('tournament_register', tournament_id=tournament_id)
        
        # ✅ IMPORTANT: Check if team is PENDING (already selected by someone with payment)
        team_pending = TournamentRegistration.objects.filter(
            tournament=tournament,
            selected_team=team,
            is_paid=True  # শুধু paid registrations check করব
        ).exclude(player=request.user).exists()
        
        if team_pending:
            messages.error(request, f"❌ Team '{team.name}' is currently pending payment by another player. Please select another team.")
            return redirect('tournament_register', tournament_id=tournament_id)
        
        try:
            # Create registration
            registration = TournamentRegistration.objects.create(
                player=request.user,
                tournament=tournament,
                selected_team=team,
                is_paid=False,
                payment_confirmed=False
            )
            
            messages.success(request, f"✅ Team '{team.name}' selected successfully! Please complete payment.")
            return redirect('payment_page', registration_id=registration.id)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, "An error occurred during registration. Please try again.")
            return redirect('tournament_register', tournament_id=tournament_id)
    
    # Get all teams
    teams = Team.objects.all().order_by('name')
    
    # ✅ Get teams that are already CONFIRMED in this tournament
    confirmed_taken_teams = TournamentRegistration.objects.filter(
        tournament=tournament,
        payment_confirmed=True
    ).values_list('selected_team_id', flat=True)
    
    # ✅ Get teams that are PENDING (paid but not confirmed) in this tournament
    pending_teams = TournamentRegistration.objects.filter(
        tournament=tournament,
        is_paid=True,
        payment_confirmed=False
    ).values_list('selected_team_id', flat=True)
    
    # ✅ Prepare team data with availability status
    team_data = []
    for team in teams:
        is_confirmed_taken = team.id in confirmed_taken_teams
        is_pending = team.id in pending_teams
        is_available = not (is_confirmed_taken or is_pending)
        
        team_data.append({
            'id': team.id,
            'name': team.name,
            'country': team.country,
            'logo': team.logo,
            'flag_url': team.get_flag_url(),
            'is_confirmed_taken': is_confirmed_taken,
            'is_pending': is_pending,
            'is_available': is_available,
        })
    
    # Check tournament capacity
    total_registered = TournamentRegistration.objects.filter(
        tournament=tournament,
        payment_confirmed=True
    ).count()
    
    tournament_full = total_registered >= tournament.max_teams
    
    context = {
        'tournament': tournament,
        'teams': team_data,
        'confirmed_taken_teams': list(confirmed_taken_teams),
        'pending_teams': list(pending_teams),
        'total_registered': total_registered,
        'tournament_full': tournament_full,
        'remaining_slots': max(0, tournament.max_teams - total_registered),
    }
    
    return render(request, 'core/tournament_register.html', context)


# -----------------------------------------------------
# Payment Page
# -----------------------------------------------------
@login_required
def payment_page(request, registration_id):
    """Payment page after team selection"""
    registration = get_object_or_404(
        TournamentRegistration, 
        id=registration_id, 
        player=request.user,
        payment_confirmed=False  # শুধু unconfirmed registration
    )
    
    if request.method == 'POST':
        # Get form data
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')
        mobile_number = request.POST.get('mobile_number')
        
        # Validate required fields
        if not payment_method or not transaction_id or not mobile_number:
            messages.error(request, "Please fill all payment details!")
            return redirect('payment_page', registration_id=registration_id)
        
        # Check if team is still available (double-check before payment)
        team_still_available = not TournamentRegistration.objects.filter(
            tournament=registration.tournament,
            selected_team=registration.selected_team,
            payment_confirmed=True
        ).exclude(id=registration_id).exists()
        
        if not team_still_available:
            messages.error(request, f"⚠️ Sorry! Team '{registration.selected_team.name}' was taken by another player while you were processing payment.")
            registration.delete()
            return redirect('tournament_register', tournament_id=registration.tournament.id)
        
        # Also check if team is pending by someone else (extra safety)
        team_pending_by_others = TournamentRegistration.objects.filter(
            tournament=registration.tournament,
            selected_team=registration.selected_team,
            is_paid=True,
            payment_confirmed=False
        ).exclude(id=registration_id).exclude(player=request.user).exists()
        
        if team_pending_by_others:
            messages.error(request, f"⚠️ Sorry! Another player has already submitted payment for team '{registration.selected_team.name}'.")
            registration.delete()
            return redirect('tournament_register', tournament_id=registration.tournament.id)
        
        try:
            # Update registration with payment info
            registration.is_paid = True
            registration.payment_method = payment_method
            registration.transaction_id = transaction_id.strip()
            registration.mobile_number = mobile_number.strip()
            registration.payment_date = timezone.now()
            registration.save()
            
            messages.success(request, "Payment submitted! Admin will verify and confirm.")
            return redirect('home')
            
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            messages.error(request, "An error occurred during payment. Please try again.")
    
    context = {
        'registration': registration,
        'tournament': registration.tournament,
        'team': registration.selected_team,
    }
    return render(request, 'core/payment_page.html', context)


# -----------------------------------------------------
# ⭐ Cancel Registration
# -----------------------------------------------------
@login_required
def cancel_registration(request, registration_id):
    """Allow user to cancel their pending registration"""
    registration = get_object_or_404(
        TournamentRegistration,
        id=registration_id,
        player=request.user
    )

    # If already paid and confirmed, do NOT allow cancellation
    if registration.payment_confirmed:
        messages.error(request, "You cannot cancel after payment confirmation.")
        return redirect("home")
    
    # If already paid (pending admin confirmation), show warning
    if registration.is_paid and not registration.payment_confirmed:
        messages.warning(request, "Your payment has been submitted. Please contact admin if you want to cancel.")
        return redirect("home")

    if request.method == "POST":
        team_name = registration.selected_team.name
        registration.delete()
        messages.success(request, f"Your registration for team '{team_name}' has been cancelled.")
        return redirect("home")

    context = {
        'registration': registration
    }
    return render(request, 'core/cancel_registration.html', context)


# -----------------------------------------------------
# ⭐ NEW — Manage Registrations for Superuser
# -----------------------------------------------------
@login_required
def manage_registrations(request):
    """Superuser can see all registrations and confirm payments"""
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to access this page.")
        return redirect("home")

    registrations = TournamentRegistration.objects.all().select_related('player', 'tournament', 'selected_team')
    
    # Check for duplicate team selections
    duplicate_teams = []
    if request.method == 'GET':
        # Find tournaments where same team selected by multiple confirmed players
        tournament_stats = TournamentRegistration.objects.filter(
            payment_confirmed=True
        ).values(
            'tournament__name', 
            'selected_team__name'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for stat in tournament_stats:
            duplicate_teams.append({
                'tournament': stat['tournament__name'],
                'team': stat['selected_team__name'],
                'count': stat['count']
            })

    if request.method == 'POST':
        action = request.POST.get('action')
        reg_id = request.POST.get('registration_id')
        registration = get_object_or_404(TournamentRegistration, id=reg_id)
        
        if action == 'confirm_payment':
            # ✅ Double-check if team is still available
            team_already_taken = TournamentRegistration.objects.filter(
                tournament=registration.tournament,
                selected_team=registration.selected_team,
                payment_confirmed=True
            ).exclude(id=reg_id).exists()
            
            if team_already_taken:
                messages.error(request, f"Cannot confirm! Team '{registration.selected_team.name}' is already taken by another confirmed player in this tournament.")
            else:
                registration.is_paid = True
                registration.payment_confirmed = True
                registration.confirmed_by = request.user
                registration.confirmed_date = timezone.now()
                registration.save()
                messages.success(request, f"✅ Payment confirmed for {registration.player.username}!")
                
        elif action == 'delete':
            registration.delete()
            messages.success(request, f"Registration deleted for {registration.player.username}!")
        
        elif action == 'reject_payment':
            registration.is_paid = False
            registration.payment_method = ''
            registration.transaction_id = ''
            registration.mobile_number = ''
            registration.payment_date = None
            registration.save()
            messages.success(request, f"Payment rejected for {registration.player.username}!")
        
        return redirect('manage_registrations')

    context = {
        'registrations': registrations,
        'duplicate_teams': duplicate_teams,
    }
    return render(request, 'core/manage_registrations.html', context)


# -----------------------------------------------------
# ⭐ Team Availability Check API
# -----------------------------------------------------
@login_required
def check_team_availability(request, tournament_id):
    """API endpoint to check team availability"""
    if request.method == 'GET' and request.is_ajax():
        tournament = get_object_or_404(Tournament, id=tournament_id)
        team_id = request.GET.get('team_id')
        
        if team_id:
            team = get_object_or_404(Team, id=team_id)
            
            # Check if team is confirmed taken
            is_confirmed_taken = TournamentRegistration.objects.filter(
                tournament=tournament,
                selected_team=team,
                payment_confirmed=True
            ).exists()
            
            # Check if team is pending
            is_pending = TournamentRegistration.objects.filter(
                tournament=tournament,
                selected_team=team,
                is_paid=True,
                payment_confirmed=False
            ).exists()
            
            return JsonResponse({
                'team_id': team_id,
                'team_name': team.name,
                'is_confirmed_taken': is_confirmed_taken,
                'is_pending': is_pending,
                'is_available': not (is_confirmed_taken or is_pending),
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# -----------------------------------------------------
# ⭐ Tournament Dashboard
# -----------------------------------------------------
@login_required
def tournament_dashboard(request, tournament_id):
    """Dashboard showing tournament details and team selections"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Use the requested tournament as the active one for this dashboard
    active_tournament = tournament

    # Get all registrations with payment confirmed
    confirmed_registrations = TournamentRegistration.objects.filter(
        tournament=tournament,
        payment_confirmed=True
    ).select_related('player', 'selected_team').order_by('selected_team__name')
    
    # Get available teams
    all_teams = Team.objects.all().order_by('name')
    taken_team_ids = confirmed_registrations.values_list('selected_team_id', flat=True)
    available_teams = all_teams.exclude(id__in=taken_team_ids)
    
    # Check if user is registered
    user_registered = TournamentRegistration.objects.filter(
        player=request.user,
        tournament=tournament,
        payment_confirmed=True
    ).exists()
    
    # Determine the user's registration object (if any) for this tournament
    user_registration = None
    if request.user.is_authenticated and not getattr(request.user, 'is_admin', False) and tournament:
        user_registration = TournamentRegistration.objects.filter(
            player=request.user,
            tournament=tournament
        ).first()
    
    context = {
        'active_tournament': active_tournament,
        'user_registration': user_registration,
        'tournament': tournament,
        'confirmed_registrations': confirmed_registrations,
        'available_teams': available_teams,
        'user_registered': user_registered,
        'total_registered': confirmed_registrations.count(),
        'max_teams': tournament.max_teams,
    }
    
    return render(request, 'core/tournament_dashboard.html', context)