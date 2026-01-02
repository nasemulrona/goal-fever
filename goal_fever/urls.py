from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Direct import from core views
from core.views import (
    home_view, 
    tournament_register, 
    payment_page, 
    cancel_registration,
    manage_registrations  # Superuser management page
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Direct URLs - no namespace conflict
    path('', home_view, name='home'),
    path('tournament/register/<int:tournament_id>/', tournament_register, name='tournament_register'),
    path('payment/<int:registration_id>/', payment_page, name='payment_page'),

    # Cancel Registration URL
    path('cancel-registration/<int:registration_id>/', cancel_registration, name='cancel_registration'),

    # Superuser Manage Registrations Page
    path('manage-registrations/', manage_registrations, name='manage_registrations'),
    
    # Other apps
    path('accounts/', include('accounts.urls')),
    path('tournaments/', include('tournaments.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
