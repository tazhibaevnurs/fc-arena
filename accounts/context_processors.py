from django.core.cache import cache
from .models import UserProfile


def ads_manager(request):
    """
    Контекстный процессор для управления рекламными блоками.
    Если пользователь авторизован и subscription_type != 'FREE' (PRO) — реклама скрыта (пустой словарь).
    Для бесплатного тарифа возвращает словарь ads с ключами header, sidebar, interstitial (заглушки AdSense/РСЯ).
    """
    ads = {}
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and getattr(profile, 'subscription_type', 'FREE').upper() != 'FREE':
            return {'ads': ads}
    # Заглушки для кода AdSense / РСЯ (подставьте свои ca-pub-... и R-A-... в админке или через AdSettings)
    placeholder_header = (
        '<!-- AdSense/РСЯ: header (leaderboard) -->'
        '<div class="ad-placeholder" data-slot="header" style="min-height:90px;display:flex;align-items:center;justify-content:center;'
        'background:rgba(30,41,59,0.5);border-radius:8px;color:#94a3b8;font-size:0.85rem;">Реклама</div>'
    )
    placeholder_sidebar = (
        '<!-- AdSense/РСЯ: sidebar -->'
        '<div class="ad-placeholder" data-slot="sidebar" style="min-height:250px;display:flex;align-items:center;justify-content:center;'
        'background:rgba(30,41,59,0.5);border-radius:8px;color:#94a3b8;font-size:0.85rem;">Реклама</div>'
    )
    placeholder_interstitial = (
        '<!-- AdSense/РСЯ: interstitial (между контентом) -->'
        '<div class="ad-placeholder" data-slot="interstitial" style="min-height:250px;display:flex;align-items:center;justify-content:center;'
        'background:rgba(30,41,59,0.5);border-radius:8px;color:#94a3b8;font-size:0.85rem;">Реклама</div>'
    )
    ads = {
        'header': placeholder_header,
        'sidebar': placeholder_sidebar,
        'interstitial': placeholder_interstitial,
    }
    return {'ads': ads}


def _get_ad_settings():
    """Кэшированные настройки рекламы для context processor (AdSense/Яндекс.RTB)."""
    from tournament.models import AdSettings
    cached = cache.get('fc26_ad_settings')
    if cached is not None:
        return cached
    try:
        s = AdSettings.get_settings()
        cache.set('fc26_ad_settings', s, 300)
        return s
    except Exception:
        return None


def saas_context(request):
    """
    Контекст для управления рекламой и подпиской.
    show_ads = False, если у пользователя активная подписка ИЛИ subscription_type != 'FREE' (PRO).
    Полностью скрываем рекламу для PRO.
    """
    show_ads = True
    has_active_subscription = False
    is_pro = False
    ad_settings = _get_ad_settings()
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile:
            has_active_subscription = profile.has_active_subscription
            is_pro = getattr(profile, 'is_pro', False)
            # Скрыть рекламу: активная подписка ИЛИ тип подписки PRO (без рекламы)
            if has_active_subscription or getattr(profile, 'subscription_type', 'FREE') == 'PRO':
                show_ads = False
    show_google_login = False
    try:
        from allauth.socialaccount.models import SocialApp
        show_google_login = SocialApp.objects.filter(provider='google').exists()
    except Exception:
        pass
    from django.conf import settings as django_settings
    return {
        'show_ads': show_ads,
        'has_active_subscription': has_active_subscription,
        'show_google_login': show_google_login,
        'is_pro': is_pro,
        'subscription_price_monthly': '$6/мес',
        'subscription_price_yearly': '$55/год',
        'ad_settings': ad_settings,
        'ads_global_enabled': ad_settings.ads_global_enabled if ad_settings else True,
        'ga4_measurement_id': getattr(django_settings, 'GA4_MEASUREMENT_ID', '') or '',
        'yandex_metrika_id': getattr(django_settings, 'YANDEX_METRIKA_ID', '') or '',
    }
