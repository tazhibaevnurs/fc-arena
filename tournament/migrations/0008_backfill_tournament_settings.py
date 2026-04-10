# Data migration: link existing Groups, Players, Matches to the single existing Settings (global tournament)

from django.db import migrations


def backfill_settings(apps, schema_editor):
    Settings = apps.get_model('tournament', 'Settings')
    Group = apps.get_model('tournament', 'Group')
    Player = apps.get_model('tournament', 'Player')
    Match = apps.get_model('tournament', 'Match')
    global_settings = Settings.objects.filter(owner__isnull=True).first()
    if not global_settings:
        return
    Group.objects.filter(settings__isnull=True).update(settings=global_settings)
    Player.objects.filter(settings__isnull=True).update(settings=global_settings)
    Match.objects.filter(settings__isnull=True).update(settings=global_settings)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0007_alter_settings_options_group_settings_match_settings_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_settings, noop),
    ]
