from django.contrib import admin
from .models import Team, Tournament, TournamentRegistration, Match, Schedule
from django.utils import timezone
from django.db.models import Count

# ==========================
# TEAM ADMIN
# ==========================
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'taken_in_tournaments')
    search_fields = ('name', 'country')
    ordering = ('name',)
    
    def taken_in_tournaments(self, obj):
        taken_count = TournamentRegistration.objects.filter(
            selected_team=obj, 
            payment_confirmed=True
        ).count()
        return taken_count
    taken_in_tournaments.short_description = 'Taken Count'


# ==========================
# TOURNAMENT ADMIN
# ==========================
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'start_date',
        'end_date',
        'registration_deadline',
        'entry_fee',
        'status',
        'is_active'
    )
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('-start_date',)


# ==========================
# TOURNAMENT REGISTRATION ADMIN
# ==========================
@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'player',
        'tournament', 
        'selected_team', 
        'payment_status',
        'mobile_number', 
        'transaction_id', 
        'payment_method', 
        'payment_confirmed',
        'confirmed_by_display'
    )
    list_filter = ('payment_confirmed', 'is_paid', 'tournament', 'payment_method')
    search_fields = ('player__username', 'transaction_id', 'mobile_number', 'selected_team__name')
    list_editable = ('payment_confirmed',)
    readonly_fields = ('registration_date', 'payment_date', 'confirmed_date')
    actions = ['confirm_payments', 'reject_payments']
    
    fieldsets = (
        ('Registration Info', {
            'fields': ('player', 'tournament', 'selected_team', 'registration_date')
        }),
        ('Payment Details', {
            'fields': ('is_paid', 'payment_method', 'transaction_id', 
                      'mobile_number', 'payment_date')
        }),
        ('Confirmation', {
            'fields': ('payment_confirmed', 'confirmed_by', 'confirmed_date')
        }),
    )
    
    def payment_status(self, obj):
        if obj.payment_confirmed:
            return '✅ Confirmed'
        elif obj.is_paid:
            return '⏳ Pending'
        else:
            return '❌ Not Paid'
    payment_status.short_description = 'Status'
    
    def confirmed_by_display(self, obj):
        if obj.confirmed_by:
            return obj.confirmed_by.username
        return "Not confirmed"
    confirmed_by_display.short_description = 'Confirmed By'
    
    def confirm_payments(self, request, queryset):
        success_count = 0
        failed_count = 0
        failed_teams = []
        
        for registration in queryset:
            # Check if team is already taken by another confirmed registration
            team_already_taken = TournamentRegistration.objects.filter(
                tournament=registration.tournament,
                selected_team=registration.selected_team,
                payment_confirmed=True
            ).exclude(id=registration.id).exists()
            
            if team_already_taken:
                failed_count += 1
                failed_teams.append(f"{registration.selected_team.name} ({registration.player.username})")
            else:
                registration.payment_confirmed = True
                registration.confirmed_by = request.user
                registration.confirmed_date = timezone.now()
                registration.save()
                success_count += 1
        
        if success_count > 0:
            self.message_user(request, f'{success_count} payments confirmed.')
        if failed_count > 0:
            self.message_user(request, 
                f'{failed_count} payments failed. Teams already taken by other confirmed players: {", ".join(set(failed_teams))}', 
                level='ERROR'
            )
    
    def reject_payments(self, request, queryset):
        updated = queryset.update(
            is_paid=False,
            payment_confirmed=False,
            transaction_id='',
            mobile_number='',
            payment_method='',
            confirmed_by=None,
            confirmed_date=None
        )
        self.message_user(request, f'{updated} payments rejected.')
    
    confirm_payments.short_description = "Confirm selected payments (with team check)"
    reject_payments.short_description = "Reject selected payments"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(player=request.user)
    
    def save_model(self, request, obj, form, change):
        """Save model with team availability check"""
        if obj.payment_confirmed and change:
            # Check if team is already taken by another confirmed registration
            team_already_taken = TournamentRegistration.objects.filter(
                tournament=obj.tournament,
                selected_team=obj.selected_team,
                payment_confirmed=True
            ).exclude(id=obj.id).exists()
            
            if team_already_taken:
                from django.contrib import messages
                messages.error(request, f"Cannot confirm! Team '{obj.selected_team.name}' is already taken by another confirmed player.")
                return
        
        if obj.payment_confirmed and not obj.confirmed_by:
            obj.confirmed_by = request.user
            obj.confirmed_date = timezone.now()
        
        super().save_model(request, obj, form, change)


# ==========================
# MATCH ADMIN
# ==========================
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tournament',
        'player1',
        'player2',
        'match_date',
        'status',
        'confirmed_by_admin'
    )
    list_filter = ('status', 'tournament', 'confirmed_by_admin')
    search_fields = ('player1__username', 'player2__username')
    ordering = ('-match_date',)


# ==========================
# SCHEDULE ADMIN
# ==========================
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tournament',
        'round_number',
        'is_published',
        'published_date'
    )
    list_filter = ('is_published', 'tournament')
    ordering = ('round_number',)