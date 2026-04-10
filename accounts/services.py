# -*- coding: utf-8 -*-
"""Сервисы для аккаунтов: игровые профили (PRO/FREE)."""
from accounts.models import GameProfile, ProfileStats, UserProfile


def user_is_pro(user):
    if not user or not user.is_authenticated:
        return False
    profile = UserProfile.objects.filter(user=user).first()
    return profile and getattr(profile, 'is_pro', False)


def get_or_create_default_game_profile(user):
    """
    Возвращает единственный профиль для FREE или основной для PRO.
    Для FREE создаёт один профиль с nickname = username, если его ещё нет.
    """
    if not user or not user.is_authenticated:
        return None
    is_pro = user_is_pro(user)
    profiles = list(GameProfile.objects.filter(user=user).order_by('-is_primary', 'created_at'))
    if not profiles:
        nickname = user.get_username() or f'Player_{user.id}'
        profile = GameProfile.objects.create(
            user=user,
            nickname=nickname,
            is_primary=True,
        )
        ProfileStats.objects.get_or_create(game_profile=profile)
        return profile
    if is_pro:
        primary = next((p for p in profiles if p.is_primary), None)
        return primary or profiles[0]
    return profiles[0]


def get_profiles_for_user(user):
    """Список профилей пользователя (для выбора в турнире). FREE — один элемент."""
    if not user or not user.is_authenticated:
        return []
    return list(GameProfile.objects.filter(user=user).order_by('-is_primary', 'created_at'))


def can_add_game_profile(user):
    """PRO может создавать несколько профилей; FREE — только один."""
    if not user or not user.is_authenticated:
        return False
    if not user_is_pro(user):
        return GameProfile.objects.filter(user=user).count() == 0
    return True
