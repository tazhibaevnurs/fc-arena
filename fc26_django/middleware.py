"""
Автоопределение языка по IP: при первом заходе (нет cookie) выбираем язык по стране из геолокации IP.
"""
import logging
import urllib.request
import urllib.error
import json
from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Страна (ISO 3166-1 alpha-2) → код языка Django
COUNTRY_TO_LANGUAGE = {
    'RU': 'ru', 'BY': 'ru', 'KZ': 'kk', 'KG': 'ru', 'TJ': 'ru', 'TM': 'ru', 'UZ': 'ru',
    'UA': 'uk',
    'US': 'en', 'GB': 'en', 'AU': 'en', 'CA': 'en', 'IE': 'en', 'NZ': 'en', 'ZA': 'en',
    'DE': 'de', 'AT': 'de', 'CH': 'de',
    'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es', 'CL': 'es', 'PE': 'es',
    'FR': 'fr', 'BE': 'fr', 'LU': 'fr',
    'PT': 'pt', 'BR': 'pt',
    'IT': 'it', 'NL': 'nl', 'PL': 'pl', 'TR': 'tr', 'JA': 'ja', 'ZH': 'zh-hans',
}
# Язык по умолчанию, если страна не в списке или геолокация недоступна
DEFAULT_LANG = 'en'


def get_client_ip(request):
    """Реальный IP клиента с учётом X-Forwarded-For (прокси/балансировщик)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_country_from_ip(ip):
    """
    Определение страны по IP через бесплатный API ip-api.com.
    Лимит: 45 запросов в минуту с одного IP. Для продакшена лучше GeoIP2 + MaxMind DB.
    """
    if not ip or ip in ('127.0.0.1', '::1', 'localhost'):
        return None
    url = f'http://ip-api.com/json/{ip}?fields=countryCode'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FC-Arena/1.0'})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get('countryCode')
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        logger.debug('GeoIP lookup failed for %s: %s', ip, e)
        return None


def get_language_from_ip(request):
    """
    Язык по IP: страна → код языка; только из списка LANGUAGES.
    Если страна неизвестна или не в списке — возвращаем 'en' (для зарубежных пользователей).
    """
    ip = get_client_ip(request)
    country = get_country_from_ip(ip)
    supported = {code for code, _ in getattr(settings, 'LANGUAGES', [])}
    if country:
        lang = COUNTRY_TO_LANGUAGE.get(country.upper())
        if lang and lang in supported:
            return lang
    # Для неизвестной страны или при недоступности геолокации — английский по умолчанию (зарубеж)
    return DEFAULT_LANG if DEFAULT_LANG in supported else None


class LocaleFromIPMiddleware(MiddlewareMixin):
    """
    Если у пользователя ещё нет cookie языка (django_language), определяем язык по IP
    и выставляем его для запроса + ставим cookie в ответе.
    """

    def process_request(self, request):
        cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        if cookie_name in request.COOKIES:
            return
        lang = get_language_from_ip(request)
        if not lang:
            return
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        request._locale_from_ip = lang

    def process_response(self, request, response):
        lang = getattr(request, '_locale_from_ip', None)
        if not lang:
            return response
        cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        max_age = getattr(settings, 'LANGUAGE_COOKIE_AGE', 365 * 24 * 60 * 60) or 365 * 24 * 60 * 60
        response.set_cookie(
            cookie_name,
            lang,
            max_age=max_age,
            path=getattr(settings, 'LANGUAGE_COOKIE_PATH', '/'),
            domain=settings.LANGUAGE_COOKIE_DOMAIN or None,
            secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
            httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        )
        return response
