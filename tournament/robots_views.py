# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.generic import View


class RobotsTxtView(View):
    """Отдаёт robots.txt с Allow, Disallow и Sitemap."""

    def get(self, request):
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        sitemap_url = f'{scheme}://{host}/sitemap.xml'
        lines = [
            'User-agent: *',
            'Allow: /',
            'Disallow: /admin/',
            'Disallow: /accounts/',
            '',
            f'Sitemap: {sitemap_url}',
        ]
        return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
