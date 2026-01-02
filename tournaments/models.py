# tournaments/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Team(models.Model):
    """Football Team Model"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    flag_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def get_flag_url(self):
        if self.flag_url:
            return self.flag_url
        
        default_flags = {
            'Argentina': 'https://flagcdn.com/w80/ar.png',
            'Brazil': 'https://flagcdn.com/w80/br.png',
            'France': 'https://flagcdn.com/w80/fr.png',
            'Germany': 'https://flagcdn.com/w80/de.png',
            'Spain': 'https://flagcdn.com/w80/es.png',
            'England': 'https://flagcdn.com/w80/gb-eng.png',
            'Italy': 'https://flagcdn.com/w80/it.png',
            'Portugal': 'https://flagcdn.com/w80/pt.png',
            'Netherlands': 'https://flagcdn.com/w80/nl.png',
            'Belgium': 'https://flagcdn.com/w80/be.png',
            'Croatia': 'https://flagcdn.com/w80/hr.png',
            'Denmark': 'https://flagcdn.com/w80/dk.png',
            'Switzerland': 'https://flagcdn.com/w80/ch.png',
            'Uruguay': 'https://flagcdn.com/w80/uy.png',
            'Mexico': 'https://flagcdn.com/w80/mx.png',
            'USA': 'https://flagcdn.com/w80/us.png',
            'Japan': 'https://flagcdn.com/w80/jp.png',
            'South Korea': 'https://flagcdn.com/w80/kr.png',
            'Australia': 'https://flagcdn.com/w80/au.png',
            'Morocco': 'https://flagcdn.com/w80/ma.png',
            'Senegal': 'https://flagcdn.com/w80/sn.png',
            'Egypt': 'https://flagcdn.com/w80/eg.png',
            'Nigeria': 'https://flagcdn.com/w80/ng.png',
            'Ghana': 'https://flagcdn.com/w80/gh.png',
            'Cameroon': 'https://flagcdn.com/w80/cm.png',
            'Chile': 'https://flagcdn.com/w80/cl.png',
            'Colombia': 'https://flagcdn.com/w80/co.png',
            'Peru': 'https://flagcdn.com/w80/pe.png',
            'Ecuador': 'https://flagcdn.com/w80/ec.png',
            'Paraguay': 'https://flagcdn.com/w80/py.png',
            'Sweden': 'https://flagcdn.com/w80/se.png',
            'Norway': 'https://flagcdn.com/w80/no.png',
        }
        return default_flags.get(self.name, 'https://flagcdn.com/w80/un.png')

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    max_teams = models.IntegerField(default=32)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class TournamentRegistration(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    selected_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    payment_confirmed = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)  # bKash/Nagad
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='confirmed_registrations')
    confirmed_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['player', 'tournament']
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'selected_team', 'payment_confirmed'],
                condition=models.Q(payment_confirmed=True),
                name='unique_team_per_tournament'
            )
        ]
    
    def clean(self):
        """Validate that team is not already taken in this tournament"""
        # চেক করো যে এই টুর্নামেন্টে এই টিম ইতিমধ্যে নেওয়া হয়েছে কিনা
        existing_registration = TournamentRegistration.objects.filter(
            tournament=self.tournament,
            selected_team=self.selected_team,
            payment_confirmed=True
        ).exclude(id=self.id).first()
        
        if existing_registration:
            raise ValidationError(
                f'Team {self.selected_team.name} is already selected by {existing_registration.player.username}'
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.player.username} - {self.tournament.name} - {self.selected_team.name}"
    
    def get_status_display(self):
        if self.payment_confirmed:
            return "Confirmed"
        elif self.is_paid:
            return "Pending"
        else:
            return "Not Paid"
    
    def get_payment_info(self):
        if self.payment_method and self.transaction_id:
            return f"{self.payment_method} - {self.transaction_id}"
        return "No payment info"

class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player1_matches')
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player2_matches')
    player1_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='player1_team')
    player2_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='player2_team')
    match_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    screenshot = models.ImageField(upload_to='match_screenshots/', blank=True, null=True)
    confirmed_by_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.player1} vs {self.player2} - {self.tournament.name}"

class Schedule(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    round_number = models.IntegerField()
    matches = models.ManyToManyField(Match)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.tournament.name} - Round {self.round_number}"