# accounts/admin.py তৈরি করুন
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PlayerProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'is_player', 'is_admin', 'is_staff')
    list_filter = ('is_admin', 'is_player', 'is_staff', 'is_superuser')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'profile_picture', 'gaming_id', 'is_player', 'is_admin'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # যদি সুপারইউজার হয়, তাহলে অটোমেটিকভাবে is_admin=True
        if obj.is_superuser:
            obj.is_admin = True
            obj.is_player = False
        super().save_model(request, obj, form, change)

admin.site.register(User, CustomUserAdmin)
admin.site.register(PlayerProfile)