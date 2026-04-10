"""
WSGI config for fc26_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fc26_django.settings')

application = get_wsgi_application()

# Vercel + SQLite fallback: /tmp DB can exist but be empty.
# Ensure schema exists; if not, run migrations.
if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL', '').strip():
    from django.core.management import call_command
    from django.db import connection

    try:
        tables = set(connection.introspection.table_names())
    except Exception:
        tables = set()

    if 'tournament_settings' not in tables:
        call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
