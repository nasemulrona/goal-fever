# tournaments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # IMPORTANT: Remove tournament_register URL pattern
    # path('register/<int:tournament_id>/', views.tournament_register, name='tournament_register'),
    
    # Keep only these URLs
    path('schedule/', views.schedule_view, name='schedule'),
    path('my-matches/', views.my_matches, name='my_matches'),
    path('submit-screenshot/<int:match_id>/', views.submit_screenshot, name='submit_screenshot'),
    
    # Optional: team selection
    # path('team-selection/<int:registration_id>/', views.team_selection, name='team_selection'),
]