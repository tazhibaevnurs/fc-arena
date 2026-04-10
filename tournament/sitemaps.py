# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import MatchHighlight, TournamentHighlight


class StaticSitemap(Sitemap):
    """Статические страницы."""
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        names = ['index', 'setup']
        out = []
        for name in names:
            try:
                reverse(name)
                out.append(name)
            except Exception:
                pass
        try:
            reverse('subscription')
            out.append('subscription')
        except Exception:
            pass
        return out

    def location(self, item):
        return reverse(item)


class MatchHighlightSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return MatchHighlight.objects.all().order_by('-created_at')

    def location(self, obj):
        return reverse('match_highlight_public', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.created_at


class TournamentHighlightSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return TournamentHighlight.objects.all().order_by('-created_at')

    def location(self, obj):
        return reverse('tournament_highlight_public', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.created_at


sitemaps = {
    'static': StaticSitemap,
    'match_highlights': MatchHighlightSitemap,
    'tournament_highlights': TournamentHighlightSitemap,
}
