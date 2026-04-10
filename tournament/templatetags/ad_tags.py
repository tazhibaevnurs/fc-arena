# -*- coding: utf-8 -*-
from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe

register = template.Library()

CACHE_KEY = 'fc26_ad_settings'
CACHE_TIMEOUT = 300  # 5 minutes


def get_ad_settings():
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached
    from tournament.models import AdSettings
    try:
        s = AdSettings.get_settings()
        cache.set(CACHE_KEY, s, CACHE_TIMEOUT)
        return s
    except Exception:
        return None


SLOT_MAP = {
    'top': 'adsense_slot_top',
    'sidebar': 'adsense_slot_sidebar',
    'bottom': 'adsense_slot_bottom',
    'in_content': 'adsense_slot_in_content',
}


@register.simple_tag(takes_context=True)
def adsense(context, position):
    """Выводит блок Google AdSense для позиции: top, sidebar, bottom, in_content."""
    if not context.get('show_ads', True):
        return ''
    s = get_ad_settings()
    if not s or not s.ads_global_enabled or not s.adsense_enabled or not (s.adsense_client_id or '').strip():
        return ''
    slot_attr = SLOT_MAP.get(position, 'adsense_slot_top')
    slot = (getattr(s, slot_attr, None) or '').strip()
    if not slot:
        return ''
    client = s.adsense_client_id.strip()
    html = (
        '<ins class="adsbygoogle" style="display:block" '
        'data-ad-client="%s" data-ad-slot="%s" data-ad-format="auto"></ins>\n'
        '<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>'
    ) % (client, slot)
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def adsense_script(context):
    """Один раз на странице: скрипт AdSense (добавить в head)."""
    if not context.get('show_ads', True):
        return ''
    s = get_ad_settings()
    if not s or not s.ads_global_enabled or not s.adsense_enabled or not (s.adsense_client_id or '').strip():
        return ''
    client = s.adsense_client_id.strip()
    return mark_safe(
        '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=%s" '
        'crossorigin="anonymous"></script>' % client
    )


@register.simple_tag(takes_context=True)
def yandex_ads(context, position=None):
    """Выводит блок РСЯ (Яндекс). position не используется — один block_id на сайт; для совместимости с планом оставлен."""
    if not context.get('show_ads', True):
        return ''
    s = get_ad_settings()
    if not s or not s.ads_global_enabled or not s.yandex_ads_enabled or not (s.yandex_block_id or '').strip():
        return ''
    block_id = s.yandex_block_id.strip()
    return mark_safe('<div id="yandex_%s"></div>' % block_id)
