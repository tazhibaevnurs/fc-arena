# -*- coding: utf-8 -*-
"""
Декораторы для доступа к PRO-функциям (подписка).
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def subscription_required(view_func):
    """
    Требует активную PRO-подписку. Иначе редирект на страницу подписки.
    Используется для: создание хайлайтов (MatchHighlight/TournamentHighlight),
    продвинутые настройки генерации команд, расширенная статистика ProfileStats.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Войдите в аккаунт.')
            return redirect('account_login')
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile or not getattr(profile, 'is_pro', False):
            messages.info(request, 'Эта функция доступна по подписке PRO.')
            return redirect('subscription')
        return view_func(request, *args, **kwargs)
    return _wrapped
