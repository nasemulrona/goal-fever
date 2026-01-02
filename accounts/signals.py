# accounts/signals.py (যদি থাকে)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import PlayerProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_player_profile(sender, instance, created, **kwargs):
    """Create PlayerProfile when a new User is created"""
    if created and not instance.is_admin:  # শুধুমাত্র প্লেয়ারদের জন্য
        PlayerProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_player_profile(sender, instance, **kwargs):
    """Save PlayerProfile when User is saved"""
    if hasattr(instance, 'playerprofile') and not instance.is_admin:
        instance.playerprofile.save()