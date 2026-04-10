# -*- coding: utf-8 -*-
"""Обновление статистики игровых профилей после матча."""
from collections import Counter
from django.db.models import Q

from accounts.models import GameProfile, ProfileStats
from tournament.models import Match, Player


def _matches_for_profile(profile):
    """Все сыгранные матчи, где профиль участвовал (дома или в гостях)."""
    if not profile:
        return Match.objects.none()
    player_ids = list(Player.objects.filter(game_profile=profile).values_list('id', flat=True))
    if not player_ids:
        return Match.objects.none()
    return Match.objects.filter(
        is_played=True,
        home_score__isnull=False,
        away_score__isnull=False,
    ).filter(
        Q(home_player_id__in=player_ids) | Q(away_player_id__in=player_ids)
    )


def _recalc_stats_for_profile(profile):
    """Пересчитать и сохранить статистику профиля по всем его сыгранным матчам."""
    if not profile:
        return
    stats, _ = ProfileStats.objects.get_or_create(game_profile=profile)
    matches = _matches_for_profile(profile)
    matches_played = matches.count()
    matches_won = 0
    matches_lost = 0
    matches_draw = 0
    goals_scored = 0
    goals_conceded = 0
    team_counter = Counter()
    max_goals_per_match = 0
    max_goals_conceded_per_match = 0

    for m in matches:
        is_home = m.home_player_id and Player.objects.filter(id=m.home_player_id, game_profile=profile).exists()
        if is_home:
            gf = m.home_score or 0
            ga = m.away_score or 0
            team_name = m.home_player.team_name if m.home_player_id else ''
        else:
            gf = m.away_score or 0
            ga = m.home_score or 0
            team_name = m.away_player.team_name if m.away_player_id else ''
        goals_scored += gf
        goals_conceded += ga
        if team_name:
            team_counter[team_name] += 1
        if gf > max_goals_per_match:
            max_goals_per_match = gf
        if ga > max_goals_conceded_per_match:
            max_goals_conceded_per_match = ga
        if gf > ga:
            matches_won += 1
        elif gf < ga:
            matches_lost += 1
        else:
            matches_draw += 1

    winrate = (matches_won / matches_played * 100.0) if matches_played else 0.0
    most_used = team_counter.most_common(1)[0][0] if team_counter else ''

    stats.matches_played = matches_played
    stats.matches_won = matches_won
    stats.matches_lost = matches_lost
    stats.matches_draw = matches_draw
    stats.goals_scored = goals_scored
    stats.goals_conceded = goals_conceded
    stats.winrate_percent = round(winrate, 1)
    stats.max_goals_per_match = max_goals_per_match
    stats.max_goals_conceded_per_match = max_goals_conceded_per_match
    stats.most_used_team = most_used
    stats.save(update_fields=[
        'matches_played', 'matches_won', 'matches_lost', 'matches_draw',
        'goals_scored', 'goals_conceded', 'winrate_percent',
        'max_goals_per_match', 'max_goals_conceded_per_match', 'most_used_team',
    ])


def update_profile_stats_for_match(match):
    """
    Вызвать после сохранения сыгранного матча. Обновляет статистику обоих профилей.
    """
    if not match or not match.is_played:
        return
    profiles_to_update = set()
    for player in (match.home_player, match.away_player):
        if player and player.game_profile_id:
            profiles_to_update.add(player.game_profile)
    for profile in profiles_to_update:
        _recalc_stats_for_profile(profile)
        recalc_tournaments_won_for_profile(profile)


def recalc_tournaments_won_for_profile(profile):
    """Пересчитать tournaments_won для профиля (кол-во турниров, где профиль победил)."""
    if not profile:
        return
    from tournament.models import Settings
    player_ids = set(Player.objects.filter(game_profile=profile).values_list('id', flat=True))
    if not player_ids:
        return
    won = 0
    for settings in Settings.objects.all():
        final = settings.matches.filter(group__isnull=True).order_by('-round_num').first()
        winner = final.winner if final and final.is_played else None
        if not winner or not winner.id:
            continue
        if winner.id in player_ids:
            won += 1
    try:
        stats = profile.stats
        stats.tournaments_won = won
        stats.save(update_fields=['tournaments_won'])
    except ProfileStats.DoesNotExist:
        pass
