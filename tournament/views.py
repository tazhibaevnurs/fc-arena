from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from accounts.decorators import subscription_required
from .models import (
    Player, Match, Settings, Group, Team, TournamentTeamSettings, AssignedTeam,
    MatchHighlight, TournamentHighlight,
)
from .ea_fc26_teams import get_random_clubs, get_random_national_teams, get_logo_url, get_team_suggestions
from .services.team_generator import generate_teams, assign_team_to_tournament
import random


def _has_active_subscription(request):
    """Есть ли у пользователя активная подписка (без рекламы + история турниров)."""
    if not request.user.is_authenticated:
        return False
    from accounts.models import UserProfile
    profile = UserProfile.objects.filter(user=request.user).first()
    return profile and profile.has_active_subscription


def get_current_settings(request):
    """
    Текущий турнир: для авторизованных — из сессии или последний по дате;
    для гостей — единственный глобальный (owner=null).
    """
    if request.user.is_authenticated:
        tid = request.session.get('tournament_id')
        if tid:
            s = Settings.objects.filter(owner=request.user, id=tid).first()
            if s:
                return s
        s = Settings.objects.filter(owner=request.user).order_by('-created_at').first()
        if s:
            request.session['tournament_id'] = s.id
            return s
        return None
    return Settings.objects.filter(owner__isnull=True).first()


def generate_bracket(player_ids):
    """
    Олимпийская система: сетка на 2, 4, 8 или 16 участников.
    Возвращает список: (round_num, home_id, away_id, is_home, next_match_idx, winner_slot).
    next_match_idx — индекс в возвращаемом списке; -1 для финала.
    """
    n = len(player_ids)
    if n not in (2, 4, 8, 16):
        return []
    first_round_count = n // 2  # матчей в первом раунде
    num_rounds = {2: 1, 4: 2, 8: 3, 16: 4}[n]
    # смещения начала раундов в общем списке матчей
    round_starts = [0]
    for r in range(1, num_rounds):
        round_starts.append(round_starts[-1] + first_round_count // (2 ** (r - 1)))
    total_matches = n - 1
    result = []
    round_size = first_round_count
    for round_num in range(1, num_rounds + 1):
        for i in range(round_size):
            idx = len(result)
            if round_num == 1:
                home_id = player_ids[i * 2]
                away_id = player_ids[i * 2 + 1]
                next_idx = round_starts[round_num] + i // 2 if round_num < num_rounds else -1
                winner_slot = 'home' if i % 2 == 0 else 'away'
                result.append((round_num, home_id, away_id, True, next_idx, winner_slot))
            else:
                next_idx = round_starts[round_num] + i // 2 if round_num < num_rounds else -1
                winner_slot = 'home' if i % 2 == 0 else 'away'
                result.append((round_num, None, None, True, next_idx, winner_slot))
        round_size //= 2
    return result


# Color palette for players
COLORS = [
    '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e',
    '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
    '#a855f7', '#ec4899', '#f43f5e', '#06b6d4', '#10b981',
    '#f59e0b', '#ef4444', '#6366f1', '#14b8a6', '#ec4899'
]


def generate_round_robin(player_ids, double_round=False):
    """
    Generate Round Robin schedule
    Returns list of tuples: (round_num, home_id, away_id, is_home)
    """
    n = len(player_ids)
    if n < 2:
        return []

    # Handle odd number of players
    if n % 2 == 1:
        player_ids = player_ids + [None]  # None represents BYE

    n = len(player_ids)
    rounds = n - 1
    matches_per_round = n // 2

    schedule = []

    # Use circle method for round robin
    for round_num in range(1, rounds + 1):
        for i in range(matches_per_round):
            home = player_ids[i]
            away = player_ids[n - 1 - i]

            # Skip BYE matches
            if home is not None and away is not None:
                schedule.append((round_num, home, away, True))  # First leg (home)

        # Rotate players (except first)
        player_ids = [player_ids[0]] + [player_ids[-1]] + player_ids[1:-1]

    # If double round, add second leg with swapped home/away
    if double_round:
        second_leg = []
        first_round_count = len(schedule)

        for i, (round_num, home, away, is_home) in enumerate(schedule):
            # Add second leg after first set of rounds
            new_round = round_num + rounds
            second_leg.append((new_round, away, home, False))  # Swap home/away

        schedule.extend(second_leg)

    return schedule


def _head_to_head_points(player_id, opponent_ids, group_id=None):
    """Points earned by player_id in played matches vs opponent_ids (Challonge-style tie-break)."""
    points = 0
    for opp_id in opponent_ids:
        if opp_id == player_id:
            continue
        match_kw = dict(
            is_played=True,
            home_player_id__in=[player_id, opp_id],
            away_player_id__in=[player_id, opp_id],
        )
        if group_id is not None:
            match_kw['group_id'] = group_id
        matches = Match.objects.filter(**match_kw)
        for m in matches:
            if m.home_player_id == player_id:
                if m.home_score > m.away_score:
                    points += 3
                elif m.home_score == m.away_score:
                    points += 1
            else:
                if m.away_score > m.home_score:
                    points += 3
                elif m.away_score == m.home_score:
                    points += 1
    return points


def calculate_standings(settings=None, group_id=None):
    """
    Standings with Challonge-style tie-break.
    If settings is set, only players/matches of that tournament. If group_id is set, only that group.
    """
    base_filter = {}
    if settings is not None:
        base_filter['settings_id'] = settings.id
    if group_id is not None:
        players = Player.objects.filter(group_id=group_id, **base_filter)
        match_filter = {'group_id': group_id, **base_filter}
    else:
        players = Player.objects.filter(**base_filter)
        match_filter = base_filter

    standings = []

    for player in players:
        stats = {
            'id': player.id,
            'name': player.name,
            'team_name': player.team_name,
            'color': player.color,
            'logo_url': getattr(player, 'logo_url', '') or '',
            'seed': player.seed,
            'games': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_diff': 0,
            'points': 0
        }

        home_matches = Match.objects.filter(home_player=player, is_played=True, **match_filter)
        for match in home_matches:
            stats['games'] += 1
            stats['goals_for'] += match.home_score
            stats['goals_against'] += match.away_score
            if match.home_score > match.away_score:
                stats['wins'] += 1
                stats['points'] += 3
            elif match.home_score == match.away_score:
                stats['draws'] += 1
                stats['points'] += 1
            else:
                stats['losses'] += 1

        away_matches = Match.objects.filter(away_player=player, is_played=True, **match_filter)
        for match in away_matches:
            stats['games'] += 1
            stats['goals_for'] += match.away_score
            stats['goals_against'] += match.home_score
            if match.away_score > match.home_score:
                stats['wins'] += 1
                stats['points'] += 3
            elif match.away_score == match.home_score:
                stats['draws'] += 1
                stats['points'] += 1
            else:
                stats['losses'] += 1

        stats['goal_diff'] = stats['goals_for'] - stats['goals_against']
        standings.append(stats)

    # Primary sort: points, goal_diff, goals_for
    standings.sort(key=lambda x: (-x['points'], -x['goal_diff'], -x['goals_for']))

    # Tie-break: head-to-head within tied groups, then seed
    i = 0
    while i < len(standings):
        j = i
        while j < len(standings) and (
            standings[j]['points'] == standings[i]['points']
            and standings[j]['goal_diff'] == standings[i]['goal_diff']
            and standings[j]['goals_for'] == standings[i]['goals_for']
        ):
            j += 1
        if j - i > 1:
            group = standings[i:j]
            tied_ids = [s['id'] for s in group]
            for s in group:
                s['_h2h'] = _head_to_head_points(s['id'], tied_ids, group_id)
            group.sort(key=lambda x: (-x['_h2h'], x['seed']))
            standings[i:j] = group
        i = j

    return standings


def get_bracket_standings(settings=None):
    """
    Итоговые места по плей-офф: 1 — чемпион, 2 — финалист, 3–4 — полуфинал, 5–8 — четвертьфинал.
    Возвращает список словарей в формате standings для страницы победителя.
    """
    qs = Match.objects.filter(group__isnull=True).select_related('home_player', 'away_player')
    if settings is not None:
        qs = qs.filter(settings=settings)
    playoff_matches = list(qs)
    if not playoff_matches:
        return []

    final = next((m for m in playoff_matches if m.next_match_id is None), None)
    if not final or not final.is_played or not final.winner:
        return []

    ordered_ids = []
    winner = final.winner
    ordered_ids.append(winner.id)
    loser = final.home_player if final.away_player_id == winner.id else final.away_player
    if loser:
        ordered_ids.append(loser.id)

    semis = [m for m in playoff_matches if m.next_match_id == final.id]
    for m in semis:
        if m.is_played and m.home_player_id and m.away_player_id and m.winner:
            semi_loser = m.home_player if m.away_player_id == m.winner.id else m.away_player
            if semi_loser and semi_loser.id not in ordered_ids:
                ordered_ids.append(semi_loser.id)

    semi_ids = [m.id for m in semis]
    quarters = [m for m in playoff_matches if m.next_match_id in semi_ids]
    for m in quarters:
        if m.is_played and m.home_player_id and m.away_player_id and m.winner:
            q_loser = m.home_player if m.away_player_id == m.winner.id else m.away_player
            if q_loser and q_loser.id not in ordered_ids:
                ordered_ids.append(q_loser.id)

    seen = set(ordered_ids)
    for m in playoff_matches:
        for p in (m.home_player, m.away_player):
            if p and p.id not in seen:
                ordered_ids.append(p.id)
                seen.add(p.id)

    result = []
    for pos, player_id in enumerate(ordered_ids, 1):
        player = Player.objects.filter(id=player_id).first()
        if not player:
            continue
        playoff_wins = 0
        for pm in playoff_matches:
            if not pm.is_played or not pm.home_player_id or not pm.away_player_id:
                continue
            w = pm.winner
            if w and w.id == player_id:
                playoff_wins += 1
        result.append({
            'id': player.id,
            'name': player.name,
            'team_name': player.team_name,
            'color': player.color,
            'logo_url': getattr(player, 'logo_url', '') or '',
            'points': playoff_wins,
            'games': 0,
            'wins': playoff_wins,
            'draws': 0,
            'losses': 0,
            'goal_diff': 0,
            'place': pos,
            'place_label': {1: 'Чемпион', 2: 'Финалист'}.get(pos) or ('1/2 финала' if pos <= 4 else ('1/4 финала' if pos <= 8 else '')),
        })
    return result


def index(request):
    """Main page - Setup tournament (step 1: count + type, step 2: players)"""
    step = request.GET.get('step', '1')
    num_players = request.GET.get('num', '4')
    tournament_type = request.GET.get('type', 'round_robin')  # round_robin | bracket
    try:
        n = int(num_players)
        if step == '2' and 2 <= n <= 16:
            num_players = n
            if tournament_type not in ('round_robin', 'bracket'):
                tournament_type = 'round_robin'
            # для брекетов без групп: только 2, 4, 8, 16; с группами: 8, 12, 16 — валидация в setup
        else:
            step = '1'
            num_players = 4
            tournament_type = 'round_robin'
    except (TypeError, ValueError):
        step = '1'
        num_players = 4
        tournament_type = 'round_robin'
    current_settings = get_current_settings(request)
    is_double_round = current_settings.is_double_round if current_settings else False
    has_group_stage = getattr(current_settings, 'has_group_stage', False) if current_settings else False
    player_slots = [{'i': i, 'color': COLORS[i % len(COLORS)]} for i in range(num_players)]

    # Генератор клубов/сборных EA FC 26 (FREE и PRO: фильтр по звёздам для всех; PRO — доп. настройки)
    suggested_teams = []
    fill = request.GET.get('fill', '')
    pro_override = None

    def _int_or_none(val):
        try:
            return int(val) if val not in (None, '') else None
        except (TypeError, ValueError):
            return None

    if step == '2':
        # Фильтр по звёздам для всех (FREE и PRO)
        star_min = _int_or_none(request.GET.get('pro_min_star_rating'))
        star_max = _int_or_none(request.GET.get('pro_max_star_rating'))
        star_override = None
        if star_min is not None or star_max is not None:
            star_override = {'min_star_rating': star_min, 'max_star_rating': star_max}

        if request.user.is_authenticated:
            from accounts.models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile and getattr(profile, 'is_pro', False):
                pro_override = {
                    'min_rating': _int_or_none(request.GET.get('pro_min_rating')),
                    'max_rating': _int_or_none(request.GET.get('pro_max_rating')),
                    'min_star_rating': star_min,
                    'max_star_rating': star_max,
                    'exclude_top_teams': request.GET.get('pro_exclude_top_teams') == '1',
                    'tier_mode_enabled': request.GET.get('pro_tier_mode_enabled') == '1',
                    'unique_teams': request.GET.get('pro_unique_teams') == '1',
                    'change_each_round': request.GET.get('pro_change_each_round') == '1',
                    'draft_mode': request.GET.get('pro_draft_mode') == '1',
                }
            else:
                pro_override = star_override  # FREE: только фильтр по звёздам
        else:
            pro_override = star_override  # Гость: только фильтр по звёздам

    if step == '2' and fill and fill in ('clubs', 'national'):
        n = num_players
        suggested_teams = generate_teams(
            request.user,
            current_settings,
            n,
            fill=fill,
            settings_override=pro_override,
        )
        if len(suggested_teams) != n:
            suggested_teams = suggested_teams[:n] if len(suggested_teams) > n else suggested_teams + [{'name': '', 'team_name': ''}] * (n - len(suggested_teams))
    slots_with_suggested = list(zip(player_slots, suggested_teams)) if suggested_teams else [(s, None) for s in player_slots]

    # Значения фильтров из GET для подстановки в форму (звёзды — для всех; остальное — для PRO)
    pro_form = {}
    if step == '2':
        pro_form = {
            'pro_min_star_rating': request.GET.get('pro_min_star_rating', ''),
            'pro_max_star_rating': request.GET.get('pro_max_star_rating', ''),
        }
        if pro_override is not None and request.user.is_authenticated:
            from accounts.models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile and getattr(profile, 'is_pro', False):
                pro_form.update({
                    'pro_exclude_top_teams': pro_override.get('exclude_top_teams'),
                    'pro_tier_mode_enabled': pro_override.get('tier_mode_enabled'),
                    'pro_unique_teams': pro_override.get('unique_teams'),
                    'pro_change_each_round': pro_override.get('change_each_round'),
                    'pro_draft_mode': pro_override.get('draft_mode'),
                })

    from accounts.services import get_profiles_for_user
    user_game_profiles = get_profiles_for_user(request.user) if request.user.is_authenticated else []
    show_ads = not _has_active_subscription(request)
    return render(request, 'index.html', {
        'step': step,
        'num_players': num_players,
        'tournament_type': tournament_type,
        'is_double_round': is_double_round,
        'has_group_stage': has_group_stage,
        'player_slots': player_slots,
        'slots_with_suggested': slots_with_suggested,
        'fill_param': fill,
        'bracket_allowed': tournament_type == 'bracket',
        'show_ads': show_ads,
        'pro_form': pro_form,
        'user_game_profiles': user_game_profiles,
    })


def setup(request):
    """Setup tournament with players"""
    if request.method != 'POST':
        return redirect('index')

    num_players = int(request.POST.get('num_players', 4))
    tournament_type = request.POST.get('tournament_type', 'round_robin')
    if tournament_type not in (Settings.TOURNAMENT_ROUND_ROBIN, Settings.TOURNAMENT_BRACKET):
        tournament_type = Settings.TOURNAMENT_ROUND_ROBIN
    is_double_round = bool(request.POST.get('is_double_round'))
    has_group_stage = bool(request.POST.get('has_group_stage'))
    tournament_name = (request.POST.get('tournament_name') or '').strip() or 'FC Arena'
    tournament_description = (request.POST.get('tournament_description') or '').strip()

    # Get player names and optional game_profile from form (название команды обязательно; имя игрока — по желанию)
    from accounts.models import GameProfile
    players_data = []
    for i in range(num_players):
        name = request.POST.get(f'player_name_{i}', '').strip()
        team = request.POST.get(f'player_team_{i}', '').strip()
        profile_id = request.POST.get(f'player_profile_{i}', '').strip()
        if team:
            players_data.append({'name': name or team, 'team': team, 'profile_id': profile_id})

    if len(players_data) < 2:
        messages.error(request, 'Минимум 2 участника с заполненными названиями команд!')
        return redirect('index')

    if tournament_type == Settings.TOURNAMENT_BRACKET and not has_group_stage and num_players not in (2, 4, 8, 16):
        messages.error(request, 'Для олимпийской системы без групп нужно 2, 4, 8 или 16 участников.')
        return redirect('index')

    if tournament_type == Settings.TOURNAMENT_BRACKET and has_group_stage and num_players not in (8, 12, 16):
        messages.error(request, 'С групповым этапом: 8, 12 или 16 участников (по 4 в группе).')
        return redirect('index')

    user = request.user if request.user.is_authenticated else None
    has_sub = _has_active_subscription(request)

    if user is None:
        Settings.objects.filter(owner__isnull=True).delete()
    elif not has_sub:
        Settings.objects.filter(owner=user).delete()

    settings = Settings.objects.create(
        name=tournament_name,
        description=tournament_description,
        tournament_type=tournament_type,
        is_double_round=is_double_round,
        has_group_stage=has_group_stage,
        owner=user,
    )
    if user:
        request.session['tournament_id'] = settings.id
        # PRO: создать настройки генерации команд (из формы или по умолчанию)
        from accounts.models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile and getattr(profile, 'is_pro', False):
            def _int_or_none(val):
                try:
                    return int(val) if val not in (None, '') else None
                except (TypeError, ValueError):
                    return None
            TournamentTeamSettings.objects.update_or_create(
                tournament=settings,
                defaults={
                    'min_rating': _int_or_none(request.POST.get('pro_min_rating')),
                    'max_rating': _int_or_none(request.POST.get('pro_max_rating')),
                    'min_star_rating': _int_or_none(request.POST.get('pro_min_star_rating')),
                    'max_star_rating': _int_or_none(request.POST.get('pro_max_star_rating')),
                    'exclude_top_teams': request.POST.get('pro_exclude_top_teams') == '1',
                    'tier_mode_enabled': request.POST.get('pro_tier_mode_enabled') == '1',
                    'unique_teams': request.POST.get('pro_unique_teams') == '1',
                    'change_each_round': request.POST.get('pro_change_each_round') == '1',
                    'draft_mode': request.POST.get('pro_draft_mode') == '1',
                },
            )

    from accounts.services import get_or_create_default_game_profile
    default_profile = get_or_create_default_game_profile(user) if user else None
    for i, player in enumerate(players_data):
        game_profile = default_profile
        name = player['name']
        if user and player.get('profile_id'):
            try:
                pid = int(player['profile_id'])
                gp = GameProfile.objects.filter(id=pid, user=user).first()
                if gp:
                    game_profile = gp
                    if not name or name == player['team']:
                        name = gp.nickname
            except (TypeError, ValueError):
                pass
        color = COLORS[i % len(COLORS)]
        logo_url = get_logo_url(player['team']) or ''
        Player.objects.create(
            settings=settings,
            game_profile=game_profile,
            name=name,
            team_name=player['team'],
            color=color,
            seed=i + 1,
            logo_url=logo_url
        )

    # PRO: при unique_teams записываем назначенные команды
    if has_sub and user:
        from accounts.models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile and getattr(profile, 'is_pro', False):
            try:
                ts = settings.team_settings
                if ts.unique_teams:
                    for pd in players_data:
                        team_obj = Team.objects.filter(name=pd['team']).first()
                        if team_obj:
                            assign_team_to_tournament(settings, team_obj, round_num=None)
            except TournamentTeamSettings.DoesNotExist:
                pass

    players = list(settings.players.all())
    player_ids = [p.id for p in players]

    if tournament_type == Settings.TOURNAMENT_BRACKET and not has_group_stage:
        # Чистая олимпийская система
        bracket_spec = generate_bracket(player_ids)
        match_objects = []
        for round_num, home_id, away_id, is_home, next_idx, winner_slot in bracket_spec:
            m = Match.objects.create(
                settings=settings,
                round_num=round_num,
                home_player_id=home_id,
                away_player_id=away_id,
                is_home=is_home,
                winner_slot=winner_slot or '',
            )
            match_objects.append((m, next_idx))
        for m, next_idx in match_objects:
            if next_idx >= 0:
                m.next_match = match_objects[next_idx][0]
                m.save()
    elif tournament_type == Settings.TOURNAMENT_BRACKET and has_group_stage:
        # Групповой этап: по 4 команды в группе, круг в каждой группе
        teams_per_group = 4
        num_groups = num_players // teams_per_group  # 8→2, 12→3, 16→4
        group_names = ['A', 'B', 'C', 'D'][:num_groups]
        groups = []
        for i, name in enumerate(group_names):
            g = Group.objects.create(settings=settings, name='Группа %s' % name, order=i + 1)
            groups.append(g)
        for idx, player in enumerate(players):
            group_idx = idx // teams_per_group
            player.group = groups[group_idx]
            player.save(update_fields=['group'])
        for group_idx, group in enumerate(groups):
            start = group_idx * teams_per_group
            end = start + teams_per_group
            group_player_ids = player_ids[start:end]
            schedule = generate_round_robin(group_player_ids, double_round=False)
            for round_num, home_id, away_id, is_home in schedule:
                Match.objects.create(
                    settings=settings,
                    round_num=round_num,
                    home_player_id=home_id,
                    away_player_id=away_id,
                    is_home=is_home,
                    group=group,
                )
    else:
        schedule = generate_round_robin(player_ids, is_double_round)
        for round_num, home_id, away_id, is_home in schedule:
            Match.objects.create(
                settings=settings,
                round_num=round_num,
                home_player_id=home_id,
                away_player_id=away_id,
                is_home=is_home
            )

    return redirect('tournament')


def tournament(request):
    """Tournament dashboard (круговой, брекет или групповой этап)."""
    settings = get_current_settings(request)
    if not settings:
        messages.info(request, 'Создайте турнир на главной странице.')
        return redirect('index')
    is_double_round = settings.is_double_round
    tournament_type = settings.tournament_type
    has_group_stage = settings.has_group_stage
    is_bracket = tournament_type == Settings.TOURNAMENT_BRACKET

    group_blocks = []
    standings = []
    rounds = {}
    round_blocks = []
    bracket_round_names = {}

    playoff_created = False

    if has_group_stage and is_bracket:
        groups = Group.objects.filter(settings=settings).order_by('order')
        for group in groups:
            group_standings = calculate_standings(settings=settings, group_id=group.id)
            group_matches = Match.objects.filter(settings=settings, group=group).select_related('home_player', 'away_player').order_by('round_num', 'id')
            gr_rounds = {}
            for m in group_matches:
                r = m.round_num
                if r not in gr_rounds:
                    gr_rounds[r] = []
                gr_rounds[r].append(m)
            gr_round_blocks = [{'num': rnum, 'name': 'Тур %s' % rnum, 'matches': gr_rounds[rnum]} for rnum in sorted(gr_rounds.keys())]
            group_blocks.append({
                'group': group,
                'standings': group_standings,
                'round_blocks': gr_round_blocks,
            })
        total = Match.objects.filter(settings=settings, group__isnull=False).count()
        played = Match.objects.filter(settings=settings, group__isnull=False, is_played=True).count()
        playoff_created = Match.objects.filter(settings=settings, group__isnull=True).exists()
    else:
        playoff_created = False
        matches = Match.objects.filter(settings=settings).select_related('home_player', 'away_player').order_by('round_num', 'id')
        standings = calculate_standings(settings=settings)
        for match in matches:
            r = match.round_num
            if r not in rounds:
                rounds[r] = []
            rounds[r].append(match)
        total = Match.objects.filter(settings=settings).count()
        played = Match.objects.filter(settings=settings, is_played=True).count()
        # Названия раундов только для плей-офф (матчи без группы)
        if is_bracket and rounds:
            total_rounds = max(rounds.keys())
            for r in range(1, total_rounds):
                bracket_round_names[r] = '1/%d финала' % (2 ** (total_rounds - r))
            bracket_round_names[total_rounds] = 'Финал'
        for rnum in sorted(rounds.keys()):
            name = bracket_round_names.get(rnum, 'Тур %s' % rnum) if is_bracket and not has_group_stage else ('Тур %s' % rnum)
            round_blocks.append({'num': rnum, 'name': name, 'matches': rounds[rnum]})

    tournament_complete = False
    winner = None
    if has_group_stage and is_bracket:
        if playoff_created:
            final_m = Match.objects.filter(settings=settings, group__isnull=True, next_match__isnull=True).first()
            if final_m and final_m.is_played and final_m.home_player_id and final_m.away_player_id and final_m.winner:
                tournament_complete = True
                w = final_m.winner
                standings_all = calculate_standings(settings=settings)
                winner = next((s for s in standings_all if s['id'] == w.id), None)
                if not winner:
                    winner = {'id': w.id, 'name': w.name, 'team_name': w.team_name, 'color': w.color, 'logo_url': getattr(w, 'logo_url', '') or '', 'games': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0, 'goal_diff': 0, 'points': 0}
        else:
            tournament_complete = total > 0 and total == played
    elif is_bracket:
        final_matches = Match.objects.filter(settings=settings, next_match__isnull=True, group__isnull=True)
        if final_matches.exists():
            final = final_matches.first()
            tournament_complete = final.is_played and final.home_player_id and final.away_player_id
            if tournament_complete and final.winner:
                w = final.winner
                standings_all = calculate_standings(settings=settings)
                winner = next((s for s in standings_all if s['id'] == w.id), None)
                if not winner:
                    winner = {'id': w.id, 'name': w.name, 'team_name': w.team_name, 'color': w.color, 'logo_url': getattr(w, 'logo_url', '') or '', 'games': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0, 'goal_diff': 0, 'points': 0}
        else:
            tournament_complete = total > 0 and total == played
            if tournament_complete and standings:
                winner = standings[0]
    else:
        tournament_complete = total > 0 and total == played
        winner = standings[0] if tournament_complete and standings else None

    if tournament_complete and winner and is_bracket:
        standings = get_bracket_standings(settings=settings) or standings

    tournament_name = settings.name
    tournament_description = settings.description or ''
    show_ads = not _has_active_subscription(request)
    has_tournament_highlight = getattr(settings, 'highlight', None) is not None

    return render(request, 'tournament.html', {
        'standings': standings,
        'rounds': rounds,
        'round_blocks': round_blocks,
        'group_blocks': group_blocks,
        'playoff_created': playoff_created,
        'is_double_round': is_double_round,
        'is_bracket': is_bracket,
        'has_group_stage': has_group_stage,
        'bracket_round_names': bracket_round_names,
        'tournament_complete': tournament_complete,
        'winner': winner,
        'played_matches': played,
        'total_matches': total,
        'tournament_name': tournament_name,
        'tournament_description': tournament_description,
        'show_ads': show_ads,
        'has_tournament_highlight': has_tournament_highlight,
        'settings': settings,
    })


def playoff_page(request):
    """Отдельная страница плей-офф (после группового этапа)."""
    settings = get_current_settings(request)
    if not settings or not settings.has_group_stage:
        return redirect('tournament')
    playoff_matches = Match.objects.filter(settings=settings, group__isnull=True).select_related('home_player', 'away_player').order_by('round_num', 'id')
    if not playoff_matches.exists():
        return redirect('tournament')

    final = Match.objects.filter(settings=settings, group__isnull=True, next_match__isnull=True).first()
    if final and final.is_played and final.home_player_id and final.away_player_id and final.winner:
        return redirect('tournament')

    po_rounds = {}
    for m in playoff_matches:
        r = m.round_num
        if r not in po_rounds:
            po_rounds[r] = []
        po_rounds[r].append(m)
    max_round = max(po_rounds.keys()) if po_rounds else 0
    playoff_round_names = {}
    for r in range(1, max_round):
        playoff_round_names[r] = '1/%d финала' % (2 ** (max_round - r))
    playoff_round_names[max_round] = 'Финал'
    playoff_round_blocks = [{'num': rnum, 'name': playoff_round_names.get(rnum, 'Раунд %s' % rnum), 'matches': po_rounds[rnum]} for rnum in sorted(po_rounds.keys())]

    tournament_name = settings.name if settings else 'FC Arena'
    playoff_total = playoff_matches.count()
    playoff_played = playoff_matches.filter(is_played=True).count()

    show_ads = not _has_active_subscription(request)
    return render(request, 'playoff.html', {
        'tournament_name': tournament_name,
        'playoff_round_blocks': playoff_round_blocks,
        'playoff_total': playoff_total,
        'playoff_played': playoff_played,
        'show_ads': show_ads,
    })


def update_match(request, match_id):
    """Update match result; для брекета — переводим победителя в следующий матч."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    settings = get_current_settings(request)
    match = Match.objects.filter(id=match_id, settings=settings).first() if settings else None
    if not match:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'Match not found'}, status=404)
        return redirect('tournament')
    if request.method == 'POST':
        try:
            home_score = int(request.POST.get('home_score', 0))
            away_score = int(request.POST.get('away_score', 0))
        except (TypeError, ValueError):
            if is_ajax:
                return JsonResponse({'ok': False, 'error': 'Invalid score'}, status=400)
            return redirect('tournament')
        if home_score is not None and away_score is not None:
            match.home_score = home_score
            match.away_score = away_score
            match.is_played = True
            match.station = (request.POST.get('station') or '').strip()
            match.notes = (request.POST.get('notes') or '').strip()
            match.save()
            from tournament.services.profile_stats import update_profile_stats_for_match
            update_profile_stats_for_match(match)
            if match.next_match_id and match.winner_slot and match.home_player_id and match.away_player_id:
                winner = match.winner
                if winner:
                    next_m = match.next_match
                    if match.winner_slot == 'home':
                        next_m.home_player = winner
                    else:
                        next_m.away_player = winner
                    next_m.save()
        if is_ajax:
            payload = {
                'ok': True,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'station': match.station or '',
                'notes': match.notes or '',
            }
            # Проверяем, завершён ли турнир (последний матч только что сохранён)
            tournament_complete = False
            if settings.tournament_type == Settings.TOURNAMENT_ROUND_ROBIN:
                total = Match.objects.filter(settings=settings).count()
                played = Match.objects.filter(settings=settings, is_played=True).count()
                tournament_complete = total > 0 and total == played
            elif settings.tournament_type == Settings.TOURNAMENT_BRACKET:
                if getattr(settings, 'has_group_stage', False):
                    playoff_created = Match.objects.filter(settings=settings, group__isnull=True).exists()
                    if playoff_created:
                        final = Match.objects.filter(
                            settings=settings, group__isnull=True, next_match__isnull=True
                        ).first()
                        tournament_complete = (
                            final and final.is_played and final.home_player_id and final.away_player_id
                        )
                    else:
                        total = Match.objects.filter(settings=settings, group__isnull=False).count()
                        played = Match.objects.filter(
                            settings=settings, group__isnull=False, is_played=True
                        ).count()
                        tournament_complete = total > 0 and total == played
                else:
                    final = Match.objects.filter(
                        settings=settings, next_match__isnull=True, group__isnull=True
                    ).first()
                    tournament_complete = (
                        final and final.is_played and final.home_player_id and final.away_player_id
                    )
            if tournament_complete:
                payload['all_complete'] = True
                payload['redirect'] = request.build_absolute_uri(reverse('tournament'))
            return JsonResponse(payload)
    if match.group_id is None and Match.objects.filter(settings=settings, group__isnull=False).exists():
        return redirect('playoff')
    return redirect('tournament')


def group_stage_status(request):
    """API: статус группового этапа. Возвращает, показывать ли кнопку «Перейти в плей-офф»."""
    settings = get_current_settings(request)
    has_group_stage = getattr(settings, 'has_group_stage', False) if settings else False
    is_bracket = getattr(settings, 'tournament_type', '') == Settings.TOURNAMENT_BRACKET if settings else False

    group_stage_complete = False
    playoff_created = False
    if settings and has_group_stage and is_bracket:
        group_matches = Match.objects.filter(settings=settings, group__isnull=False)
        total_group = group_matches.count()
        played_group = group_matches.filter(is_played=True).count()
        group_stage_complete = total_group > 0 and total_group == played_group
        playoff_created = Match.objects.filter(settings=settings, group__isnull=True).exists()

    show_playoff_button = group_stage_complete and not playoff_created
    return JsonResponse({
        'group_stage_complete': group_stage_complete,
        'playoff_created': playoff_created,
        'show_playoff_button': show_playoff_button,
    })


def create_playoff(request):
    """Создать плей-офф сетку по итогам групп (1–2 места). Вызывается по кнопке после завершения группового этапа."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

    settings = get_current_settings(request)
    if not settings or not getattr(settings, 'has_group_stage', False) or getattr(settings, 'tournament_type', '') != Settings.TOURNAMENT_BRACKET:
        return JsonResponse({'ok': False, 'error': 'Not a group-stage bracket'}, status=400)

    group_matches = Match.objects.filter(settings=settings, group__isnull=False)
    total_group = group_matches.count()
    played_group = group_matches.filter(is_played=True).count()
    if total_group == 0 or total_group != played_group:
        return JsonResponse({'ok': False, 'error': 'Group stage not complete'}, status=400)
    if Match.objects.filter(settings=settings, group__isnull=True).exists():
        return JsonResponse({'ok': False, 'error': 'Playoff already created'}, status=400)

    groups = list(Group.objects.filter(settings=settings).order_by('order'))
    num_groups = len(groups)
    if num_groups not in (2, 4):
        return JsonResponse({'ok': False, 'error': 'Only 2 or 4 groups supported'}, status=400)

    top2_per_group = []
    for group in groups:
        st = calculate_standings(settings=settings, group_id=group.id)
        if len(st) < 2:
            return JsonResponse({'ok': False, 'error': 'Not enough teams in group'}, status=400)
        top2_per_group.append([st[0]['id'], st[1]['id']])

    if num_groups == 2:
        final = Match.objects.create(settings=settings, round_num=2, winner_slot='', group=None)
        semi1 = Match.objects.create(
            settings=settings, round_num=1, home_player_id=top2_per_group[0][0], away_player_id=top2_per_group[1][1],
            is_home=True, next_match=final, winner_slot='home', group=None
        )
        semi2 = Match.objects.create(
            settings=settings, round_num=1, home_player_id=top2_per_group[1][0], away_player_id=top2_per_group[0][1],
            is_home=True, next_match=final, winner_slot='away', group=None
        )
    else:
        final = Match.objects.create(settings=settings, round_num=3, winner_slot='', group=None)
        semi1 = Match.objects.create(settings=settings, round_num=2, is_home=True, next_match=final, winner_slot='home', group=None)
        semi2 = Match.objects.create(settings=settings, round_num=2, is_home=True, next_match=final, winner_slot='away', group=None)
        q1 = Match.objects.create(settings=settings, round_num=1, home_player_id=top2_per_group[0][0], away_player_id=top2_per_group[1][1], is_home=True, next_match=semi1, winner_slot='home', group=None)
        q2 = Match.objects.create(settings=settings, round_num=1, home_player_id=top2_per_group[2][0], away_player_id=top2_per_group[3][1], is_home=True, next_match=semi1, winner_slot='away', group=None)
        q3 = Match.objects.create(settings=settings, round_num=1, home_player_id=top2_per_group[1][0], away_player_id=top2_per_group[0][1], is_home=True, next_match=semi2, winner_slot='home', group=None)
        q4 = Match.objects.create(settings=settings, round_num=1, home_player_id=top2_per_group[3][0], away_player_id=top2_per_group[2][1], is_home=True, next_match=semi2, winner_slot='away', group=None)

    from django.urls import reverse
    return JsonResponse({'ok': True, 'redirect': reverse('playoff')})


def api_generate_teams(request):
    """
    API для генерации команд без перезагрузки страницы (AJAX).
    Кэширование на 60 сек для снижения нагрузки на VPS.
    """
    from django.core.cache import cache
    try:
        num_players = int(request.GET.get('num_players', 4))
    except (TypeError, ValueError):
        num_players = 4
    num_players = max(2, min(16, num_players))
    fill = request.GET.get('fill', 'clubs')
    if fill not in ('clubs', 'national'):
        fill = 'clubs'

    def _int_or_none(val):
        try:
            return int(val) if val not in (None, '') else None
        except (TypeError, ValueError):
            return None

    star_min = _int_or_none(request.GET.get('pro_min_star_rating'))
    star_max = _int_or_none(request.GET.get('pro_max_star_rating'))
    star_override = None
    if star_min is not None or star_max is not None:
        star_override = {'min_star_rating': star_min, 'max_star_rating': star_max}

    pro_override = None
    if request.user.is_authenticated:
        from accounts.models import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and getattr(profile, 'is_pro', False):
            pro_override = {
                'min_rating': _int_or_none(request.GET.get('pro_min_rating')),
                'max_rating': _int_or_none(request.GET.get('pro_max_rating')),
                'min_star_rating': star_min,
                'max_star_rating': star_max,
                'exclude_top_teams': request.GET.get('pro_exclude_top_teams') == '1',
                'tier_mode_enabled': request.GET.get('pro_tier_mode_enabled') == '1',
                'unique_teams': request.GET.get('pro_unique_teams') == '1',
                'change_each_round': request.GET.get('pro_change_each_round') == '1',
                'draft_mode': request.GET.get('pro_draft_mode') == '1',
            }
        else:
            pro_override = star_override
    else:
        pro_override = star_override

    settings_obj = get_current_settings(request)
    cache_key = 'fc26_teams_%s_%s_%s_%s_%s' % (
        getattr(request.user, 'id', 0),
        getattr(settings_obj, 'id', 0),
        num_players,
        fill,
        hash(frozenset((k, str(v)) for k, v in (pro_override or {}).items())),
    )
    teams = cache.get(cache_key)
    if teams is None:
        teams = generate_teams(
            request.user,
            settings_obj,
            num_players,
            fill=fill,
            settings_override=pro_override,
        )
        cache.set(cache_key, teams, 60)
    # Добиваем до num_players пустыми слотами при нехватке
    while len(teams) < num_players:
        teams.append({'name': '', 'team_name': '', 'logo_url': ''})
    teams = teams[:num_players]
    return JsonResponse({'teams': teams})


def team_suggestions(request):
    """API для автодополнения поля «Команда»: GET ?q=... возвращает JSON с вариантами (team_name, logo_url)."""
    q = (request.GET.get('q') or '').strip()
    if not q:
        return JsonResponse({'suggestions': []})
    suggestions = get_team_suggestions(q, limit=10)
    return JsonResponse({'suggestions': suggestions})


def reset_tournament(request):
    """Сброс: у подписчиков — переход на создание нового (история сохраняется); у остальных — удаление текущего турнира."""
    if request.user.is_authenticated and _has_active_subscription(request):
        request.session.pop('tournament_id', None)
        messages.info(request, 'Выберите турнир из истории или создайте новый.')
        return redirect('index')
    settings = get_current_settings(request)
    if settings:
        settings.delete()
    return redirect('index')


def tournament_history(request):
    """История турниров (только для подписчиков)."""
    if not request.user.is_authenticated:
        return redirect('account_login')
    from accounts.models import UserProfile
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile or not profile.has_active_subscription:
        messages.info(request, 'Доступ к истории турниров — по подписке.')
        return redirect('subscription')
    tournaments = Settings.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'tournament/history.html', {'tournaments': tournaments})


def tournament_select(request, tournament_id):
    """Выбор турнира из истории (подписчики): установить текущий и перейти на страницу турнира."""
    if not request.user.is_authenticated:
        return redirect('account_login')
    settings = Settings.objects.filter(owner=request.user, id=tournament_id).first()
    if not settings:
        messages.error(request, 'Турнир не найден.')
        return redirect('index')
    request.session['tournament_id'] = settings.id
    return redirect('tournament')


def _user_is_pro(request):
    if not request.user.is_authenticated:
        return False
    from accounts.models import UserProfile
    profile = UserProfile.objects.filter(user=request.user).first()
    return profile and getattr(profile, 'is_pro', False)


@subscription_required
def create_match_highlight(request, match_id):
    """PRO: создать публичную ссылку на матч (декоратор subscription_required)."""
    settings = get_current_settings(request)
    match = Match.objects.filter(id=match_id, settings=settings).first() if settings else None
    if not match:
        messages.error(request, 'Матч не найден.')
        return redirect('tournament')
    if getattr(match, 'highlight', None):
        messages.info(request, 'Публичная ссылка уже создана.')
        return redirect('tournament')
    import uuid
    from django.urls import reverse
    from django.utils.safestring import mark_safe
    slug = uuid.uuid4().hex[:16]
    MatchHighlight.objects.create(match=match, slug=slug, created_by=request.user)
    path = reverse('match_highlight_public', kwargs={'slug': slug})
    messages.success(request, mark_safe(f'Публичная ссылка на матч: <a href="{path}" class="flash-message-link">Открыть</a>'), extra_tags='safe')
    return redirect('tournament')


@subscription_required
def create_tournament_highlight(request):
    """PRO: создать публичную страницу турнира (декоратор subscription_required)."""
    settings = get_current_settings(request)
    if not settings:
        messages.error(request, 'Турнир не найден.')
        return redirect('index')
    if getattr(settings, 'highlight', None):
        messages.info(request, 'Публичная страница турнира уже создана.')
        return redirect('tournament')
    import uuid
    from django.urls import reverse
    from django.utils.safestring import mark_safe
    slug = uuid.uuid4().hex[:16]
    TournamentHighlight.objects.create(tournament=settings, slug=slug, created_by=request.user)
    path = reverse('tournament_highlight_public', kwargs={'slug': slug})
    messages.success(request, mark_safe(f'Публичная страница турнира: <a href="{path}" class="flash-message-link">Открыть</a>'), extra_tags='safe')
    return redirect('tournament')


def match_highlight_public(request, slug):
    """Публичная страница матча (PRO highlight). Без авторизации."""
    highlight = MatchHighlight.objects.filter(slug=slug).select_related('match', 'match__settings', 'match__home_player', 'match__away_player').first()
    if not highlight:
        return render(request, 'tournament/highlight_404.html', status=404)
    m = highlight.match
    stage = ''
    if m.group_id:
        stage = m.group.name if m.group else 'Групповой этап'
    else:
        stage = 'Финал' if (m.next_match_id is None) else ('1/2 финала' if m.round_num >= 2 else '1/4 финала')
    share_url = request.build_absolute_uri(request.get_full_path())
    p1_name = (m.home_player.name or m.home_player.team_name) if m.home_player else '—'
    p2_name = (m.away_player.name or m.away_player.team_name) if m.away_player else '—'
    share_text = f'Смотри результат матча {p1_name} vs {p2_name} на FC Arena: {share_url}'
    score_str = f'{m.home_score or 0} — {m.away_score or 0}' if m.is_played else '—'
    tournament_name = m.settings.name if m.settings_id else ''
    meta_description = f'Матч {p1_name} vs {p2_name} — {score_str}. Турнир: {tournament_name}. FC Arena — турнирная платформа EA Sports FC 26.'
    meta_title = f'Матч: {p1_name} vs {p2_name} — FC Arena'
    og_image = None
    for p in (m.home_player, m.away_player):
        if p and getattr(p, 'logo_url', ''):
            url = (p.logo_url or '').strip()
            if url:
                og_image = request.build_absolute_uri(url) if url.startswith('/') else url
                break
    return render(request, 'tournament/match_highlight.html', {
        'highlight': highlight,
        'match': m,
        'player1': m.home_player,
        'player2': m.away_player,
        'score': score_str,
        'tournament_name': tournament_name,
        'stage': stage,
        'share_url': share_url,
        'share_text': share_text,
        'meta_description': meta_description,
        'meta_title': meta_title,
        'og_url': share_url,
        'og_image': og_image,
        'og_site_name': 'FC Arena',
    })


def tournament_highlight_public(request, slug):
    """Публичная страница турнира (PRO highlight). Без авторизации."""
    highlight = TournamentHighlight.objects.filter(slug=slug).select_related('tournament').first()
    if not highlight:
        return render(request, 'tournament/highlight_404.html', status=404)
    settings = highlight.tournament
    is_bracket = getattr(settings, 'tournament_type', '') == Settings.TOURNAMENT_BRACKET
    has_group_stage = getattr(settings, 'has_group_stage', False)
    rounds = {}
    round_blocks = []
    group_blocks = []
    standings = []
    playoff_created = False
    winner = None
    bracket_round_names = {}

    if has_group_stage and is_bracket:
        groups = Group.objects.filter(settings=settings).order_by('order')
        for group in groups:
            group_standings = calculate_standings(settings=settings, group_id=group.id)
            group_matches = Match.objects.filter(settings=settings, group=group).select_related('home_player', 'away_player').order_by('round_num', 'id')
            gr_rounds = {}
            for m in group_matches:
                r = m.round_num
                if r not in gr_rounds:
                    gr_rounds[r] = []
                gr_rounds[r].append(m)
            gr_round_blocks = [{'num': rnum, 'name': 'Тур %s' % rnum, 'matches': gr_rounds[rnum]} for rnum in sorted(gr_rounds.keys())]
            group_blocks.append({
                'group': group,
                'standings': group_standings,
                'round_blocks': gr_round_blocks,
            })
        playoff_created = Match.objects.filter(settings=settings, group__isnull=True).exists()
        if playoff_created:
            playoff_matches = Match.objects.filter(settings=settings, group__isnull=True).select_related('home_player', 'away_player').order_by('round_num', 'id')
            for m in playoff_matches:
                r = m.round_num
                if r not in rounds:
                    rounds[r] = []
                rounds[r].append(m)
            total_rounds = max(rounds.keys()) if rounds else 0
            for r in range(1, total_rounds):
                bracket_round_names[r] = '1/%d финала' % (2 ** (total_rounds - r))
            bracket_round_names[total_rounds] = 'Финал'
            for rnum in sorted(rounds.keys()):
                round_blocks.append({'num': rnum, 'name': bracket_round_names.get(rnum, ''), 'matches': rounds[rnum]})
            final_m = Match.objects.filter(settings=settings, group__isnull=True, next_match__isnull=True).first()
            if final_m and final_m.is_played and final_m.winner:
                w = final_m.winner
                winner = {'name': w.name, 'team_name': w.team_name, 'logo_url': getattr(w, 'logo_url', '') or ''}
    else:
        matches = Match.objects.filter(settings=settings).select_related('home_player', 'away_player').order_by('round_num', 'id')
        standings = calculate_standings(settings=settings)
        for match in matches:
            r = match.round_num
            if r not in rounds:
                rounds[r] = []
            rounds[r].append(match)
        if is_bracket and rounds:
            total_rounds = max(rounds.keys())
            for r in range(1, total_rounds):
                bracket_round_names[r] = '1/%d финала' % (2 ** (total_rounds - r))
            bracket_round_names[total_rounds] = 'Финал'
        for rnum in sorted(rounds.keys()):
            name = bracket_round_names.get(rnum, 'Тур %s' % rnum) if is_bracket else ('Тур %s' % rnum)
            round_blocks.append({'num': rnum, 'name': name, 'matches': rounds[rnum]})
        if standings:
            winner = standings[0]

    share_url = request.build_absolute_uri(request.get_full_path())
    share_text = f'Я выиграл турнир {settings.name} на FC Arena! Смотри результат: {share_url}'
    total_matches = Match.objects.filter(settings=settings).count()
    num_participants = Player.objects.filter(settings=settings).count()
    winner_name = winner.get('name', '') if winner else ''
    meta_description = f'Турнир {settings.name}. Победитель: {winner_name}. Результаты и таблица на FC Arena — турнирная платформа EA Sports FC 26.' if winner_name else f'Турнир {settings.name}. Результаты на FC Arena — турнирная платформа EA Sports FC 26.'
    meta_title = f'{settings.name} — FC Arena'
    og_image = None
    if winner and winner.get('logo_url'):
        url = (winner['logo_url'] or '').strip()
        if url:
            og_image = request.build_absolute_uri(url) if url.startswith('/') else url
    return render(request, 'tournament/tournament_highlight.html', {
        'highlight': highlight,
        'tournament': settings,
        'tournament_name': settings.name,
        'tournament_description': settings.description or '',
        'standings': standings,
        'round_blocks': round_blocks,
        'group_blocks': group_blocks,
        'playoff_created': playoff_created,
        'is_bracket': is_bracket,
        'has_group_stage': has_group_stage,
        'winner': winner,
        'share_url': share_url,
        'share_text': share_text,
        'total_matches': total_matches,
        'num_participants': num_participants,
        'meta_description': meta_description,
        'meta_title': meta_title,
        'og_url': share_url,
        'og_image': og_image,
        'og_site_name': 'FC Arena',
    })
