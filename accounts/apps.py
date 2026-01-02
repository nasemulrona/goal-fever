# accounts/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    # ready মেথড রিমুভ করুন অথবা শুধু pass রাখুন
    def ready(self):
        pass  # signals import করবেন না