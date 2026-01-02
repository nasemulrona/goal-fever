from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    """Custom User Model with additional fields"""
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    gaming_id = models.CharField(max_length=50, blank=True, null=True)
    is_player = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # সুপারইউজারদের জন্য অটো is_admin=True
        if self.is_superuser:
            self.is_admin = True
            self.is_player = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username

class PlayerProfile(models.Model):
    """Extended profile for players"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_goals = models.IntegerField(default=0)
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)
    ranking = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # র‍্যাংকিং অটো ক্যালকুলেট
        if self.user.is_admin:
            # অ্যাডমিনের জন্য র‍্যাংকিং 0 রাখুন
            self.ranking = 0
        else:
            # প্লেয়ারদের র‍্যাংকিং: প্রথমে wins, তারপর goals
            all_profiles = PlayerProfile.objects.exclude(user__is_admin=True)
            
            # wins এবং goals এর ভিত্তিতে সাজান
            sorted_profiles = sorted(
                all_profiles,
                key=lambda x: (x.matches_won, x.total_goals),
                reverse=True
            )
            
            # র‍্যাংকিং সেট করুন
            for rank, profile in enumerate(sorted_profiles, 1):
                if profile.id == self.id:
                    self.ranking = rank
                    break
        
        super().save(*args, **kwargs)
    
    def win_percentage(self):
        if self.matches_played > 0:
            return (self.matches_won / self.matches_played) * 100
        return 0
    
    def __str__(self):
        return f"{self.user.username}'s Profile"