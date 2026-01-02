from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('tournament/register/<int:tournament_id>/', 
         views.tournament_register, name='tournament_register'),
    path('payment/<int:registration_id>/', views.payment_page, name='payment_page'),
    path('cancel-registration/<int:registration_id>/', views.cancel_registration, name='cancel_registration'),
    path('manage-registrations/', views.manage_registrations, name='manage_registrations'),
    path('check-team/<int:tournament_id>/', views.check_team_availability, name='check_team_availability'),
    path('tournament/<int:tournament_id>/dashboard/', views.tournament_dashboard, name='tournament_dashboard'),
]