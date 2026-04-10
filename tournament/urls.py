from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('setup/', views.setup, name='setup'),
    path('tournament/', views.tournament, name='tournament'),
    path('tournament/playoff/', views.playoff_page, name='playoff'),
    path('tournament/history/', views.tournament_history, name='tournament_history'),
    path('tournament/<int:tournament_id>/', views.tournament_select, name='tournament_select'),
    path('update_match/<int:match_id>/', views.update_match, name='update_match'),
    path('api/generate-teams/', views.api_generate_teams, name='api_generate_teams'),
    path('api/team-suggestions/', views.team_suggestions, name='team_suggestions'),
    path('api/group-stage-status/', views.group_stage_status, name='group_stage_status'),
    path('create_playoff/', views.create_playoff, name='create_playoff'),
    path('reset/', views.reset_tournament, name='reset'),
    path('highlight/match/<int:match_id>/', views.create_match_highlight, name='create_match_highlight'),
    path('highlight/tournament/', views.create_tournament_highlight, name='create_tournament_highlight'),
    # Публичные страницы (без авторизации)
    path('m/<slug:slug>/', views.match_highlight_public, name='match_highlight_public'),
    path('t/<slug:slug>/', views.tournament_highlight_public, name='tournament_highlight_public'),
]
