"""
URL configuration for fc26_django project.
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.i18n import set_language

from tournament.robots_views import RobotsTxtView
from tournament.sitemaps import sitemaps

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/setlang/', set_language, name='set_language'),
    path('robots.txt', RobotsTxtView.as_view(), name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('accounts/', include('accounts.urls')),
    path('', include('tournament.urls')),
]
