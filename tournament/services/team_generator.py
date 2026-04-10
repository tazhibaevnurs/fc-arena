# -*- coding: utf-8 -*-
"""
Сервис генерации команд для турнира.
FREE: обычный random из ea_fc26_teams.
PRO: применение настроек TournamentTeamSettings (рейтинг, тиры, уникальность, драфт).
"""
import random
from django.db import transaction

from tournament.models import Settings, Team, TournamentTeamSettings, AssignedTeam
from tournament.ea_fc26_teams import (
    get_random_clubs,
    get_random_national_teams,
    get_logo_url,
    CLUBS,
    NATIONAL_TEAMS_MEN,
)


def _user_is_pro(user):
    if not user or not user.is_authenticated:
        return False
    from accounts.models import UserProfile
    profile = UserProfile.objects.filter(user=user).first()
    return profile and getattr(profile, 'is_pro', False)


def _get_pro_pool(settings, round_num=None, exclude_team_ids=None, settings_override=None, fill='clubs'):
    """
    Строит пул команд для PRO по настройкам турнира или по переданному override (форма/GET).
    fill: 'clubs' — только мужские клубы, 'national' — только мужские сборные (без смешивания и без женских).
    """
    if settings_override is not None:
        return _get_pro_pool_from_override(settings_override, exclude_team_ids, fill)

    try:
        team_settings = settings.team_settings
    except (TournamentTeamSettings.DoesNotExist, AttributeError):
        qs = Team.objects.all()
        qs = _apply_fill_filter(qs, fill)
        return list(qs)

    qs = Team.objects.all()
    qs = _apply_fill_filter(qs, fill)

    # A) Диапазон рейтинга (числовой или звёзды)
    if getattr(team_settings, 'min_star_rating', None) is not None:
        qs = qs.filter(star_rating__gte=team_settings.min_star_rating)
    elif team_settings.min_rating is not None:
        qs = qs.filter(rating__gte=team_settings.min_rating)
    if getattr(team_settings, 'max_star_rating', None) is not None:
        qs = qs.filter(star_rating__lte=team_settings.max_star_rating)
    elif team_settings.max_rating is not None:
        qs = qs.filter(rating__lte=team_settings.max_rating)

    # B) Запрет топ-команд (rating > 88)
    if team_settings.exclude_top_teams:
        qs = qs.filter(rating__lte=88)

    # C) Tier mode — выбираем тир случайно, потом фильтруем по нему
    if team_settings.tier_mode_enabled:
        tiers = [1, 2, 3]
        chosen_tier = random.choice(tiers)
        qs = qs.filter(tier=chosen_tier)

    # Исключаем уже назначенные (unique_teams / change_each_round)
    if settings and (team_settings.unique_teams or team_settings.change_each_round):
        assigned = AssignedTeam.objects.filter(tournament=settings)
        if team_settings.change_each_round and round_num is not None:
            assigned = assigned.filter(round_num=round_num)
        else:
            assigned = assigned.filter(round_num__isnull=True)
        used_ids = set(assigned.values_list('team_id', flat=True))
        if used_ids:
            qs = qs.exclude(id__in=used_ids)
    if exclude_team_ids:
        qs = qs.exclude(id__in=exclude_team_ids)

    return list(qs)


def _apply_fill_filter(qs, fill):
    """Только мужские команды: fill=clubs — клубы, fill=national — сборные, без смешивания."""
    if fill == 'national':
        return qs.filter(name__in=NATIONAL_TEAMS_MEN)
    return qs.filter(name__in=CLUBS)


def _get_pro_pool_from_override(override, exclude_team_ids=None, fill='clubs'):
    """Пул команд по dict из GET/формы (фильтрация на шаге настройки). Только мужские: клубы или сборные по fill."""
    qs = Team.objects.all()
    qs = _apply_fill_filter(qs, fill)
    # Звёзды приоритетнее числового рейтинга
    min_star = override.get('min_star_rating')
    max_star = override.get('max_star_rating')
    if min_star is not None:
        qs = qs.filter(star_rating__gte=min_star)
    if max_star is not None:
        qs = qs.filter(star_rating__lte=max_star)
    if min_star is None and max_star is None:
        min_rating = override.get('min_rating')
        max_rating = override.get('max_rating')
        if min_rating is not None:
            qs = qs.filter(rating__gte=min_rating)
        if max_rating is not None:
            qs = qs.filter(rating__lte=max_rating)
    if override.get('exclude_top_teams'):
        qs = qs.filter(rating__lte=88)
    if override.get('tier_mode_enabled'):
        tiers = [1, 2, 3]
        chosen_tier = random.choice(tiers)
        qs = qs.filter(tier=chosen_tier)
    if exclude_team_ids:
        qs = qs.exclude(id__in=exclude_team_ids)
    return list(qs)


def _team_to_dict(team):
    """Team instance -> dict как у get_random_clubs."""
    return {
        "name": "",
        "team_name": team.name,
        "logo_url": get_logo_url(team.name) or "",
    }


def generate_teams(user, tournament, count, fill='clubs', round_num=None, settings_override=None):
    """
    Генерирует список из `count` команд для турнира.

    - FREE: использует текущую логику (get_random_clubs / get_random_national_teams).
    - PRO: применяет TournamentTeamSettings или settings_override (из GET при нажатии «Клубы»/«Сборные»).
    - settings_override: dict с min_rating, max_rating, exclude_top_teams, tier_mode_enabled и т.д. —
      чтобы фильтрация работала при генерации на шаге настройки до создания турнира.

    Возвращает список dict: {"name": "", "team_name": "...", "logo_url": "..."}.
    """
    if not _user_is_pro(user):
        # FREE — с фильтром по звёздам, если передан settings_override с min/max_star_rating
        star_min = settings_override.get('min_star_rating') if settings_override else None
        star_max = settings_override.get('max_star_rating') if settings_override else None
        if star_min is not None or star_max is not None:
            qs = Team.objects.all()
            qs = _apply_fill_filter(qs, fill)
            if star_min is not None:
                qs = qs.filter(star_rating__gte=star_min)
            if star_max is not None:
                qs = qs.filter(star_rating__lte=star_max)
            pool = list(qs)
            if not pool:
                if fill == 'national':
                    pool_result = get_random_national_teams(count, women=False)
                else:
                    pool_result = get_random_clubs(count)
                return pool_result[:count] if len(pool_result) > count else pool_result
            chosen = random.sample(pool, min(count, len(pool)))
            return [_team_to_dict(t) for t in chosen]
        # FREE без фильтра звёзд — как раньше
        if fill == 'national':
            pool_result = get_random_national_teams(count, women=False)
        else:
            pool_result = get_random_clubs(count)
        return pool_result[:count] if len(pool_result) > count else pool_result

    # PRO с переданными настройками (форма/GET на шаге 2)
    if settings_override is not None:
        pool = _get_pro_pool(None, round_num=round_num, settings_override=settings_override, fill=fill)
        if not pool:
            return _fallback_free_teams(count, fill)
        chosen = random.sample(pool, min(count, len(pool)))
        return [_team_to_dict(t) for t in chosen]

    # PRO без турнира (страница настройки до создания, без override)
    if tournament is None:
        qs = _apply_fill_filter(Team.objects.all(), fill)
        teams = list(qs)
        if not teams:
            return _fallback_free_teams(count, fill)
        chosen = random.sample(teams, min(count, len(teams)))
        return [_team_to_dict(t) for t in chosen]

    # PRO с турниром
    try:
        team_settings = tournament.team_settings
    except TournamentTeamSettings.DoesNotExist:
        qs = _apply_fill_filter(Team.objects.all(), fill)
        teams = list(qs[: count * 2])
        if not teams:
            return _fallback_free_teams(count, fill)
        chosen = random.sample(teams, min(count, len(teams)))
        return [_team_to_dict(t) for t in chosen]

    # Режим драфта: возвращаем пул для выбора
    if team_settings.draft_mode:
        pool = _get_pro_pool(tournament, round_num=round_num, fill=fill)
        return [_team_to_dict(t) for t in pool]

    pool = _get_pro_pool(tournament, round_num=round_num, fill=fill)
    if not pool:
        return _fallback_free_teams(count, fill)

    if len(pool) < count and team_settings.unique_teams:
        chosen = pool
    else:
        chosen = random.sample(pool, min(count, len(pool)))

    return [_team_to_dict(t) for t in chosen]


def _fallback_free_teams(count, fill):
    """При пустом PRO-пуле откат на FREE-логику."""
    if fill == 'national':
        return get_random_national_teams(count, women=False)[:count]
    return get_random_clubs(count)[:count]


def assign_team_to_tournament(tournament, team, round_num=None):
    """
    PRO: записать назначение команды (для unique_teams / change_each_round).
    Вызывать после того как игроку назначена команда.
    """
    if not tournament or not team:
        return
    with transaction.atomic():
        AssignedTeam.objects.get_or_create(
            tournament=tournament,
            team=team,
            round_num=round_num,
        )


def get_draft_pool(user, tournament, round_num=None):
    """
    PRO, draft_mode: возвращает пул доступных команд для выбора по очереди.
    Формат: список dict {"team_name", "logo_url", "id"}.
    """
    if not _user_is_pro(user):
        return []
    try:
        if not tournament.team_settings.draft_mode:
            return []
    except TournamentTeamSettings.DoesNotExist:
        return []
    pool = _get_pro_pool(tournament, round_num=round_num)
    return [
        {"id": t.id, "team_name": t.name, "logo_url": get_logo_url(t.name) or ""}
        for t in pool
    ]


def generate_team(user, tournament, round_num=None, exclude_team_ids=None):
    """
    Генерирует одну команду для слота (удобно для поочерёдного назначения).
    exclude_team_ids — уже выбранные team.id в текущем раунде/турнире.
    """
    teams = generate_teams(
        user, tournament, count=1, fill='clubs', round_num=round_num
    )
    if not teams:
        return None
    return teams[0]
