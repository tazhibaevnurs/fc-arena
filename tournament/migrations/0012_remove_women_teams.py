# Remove women's teams from Team — only male clubs and male national teams

from django.db import migrations


def remove_women_teams(apps, schema_editor):
    from tournament.ea_fc26_teams import NATIONAL_TEAMS_WOMEN, WOMEN_CLUBS
    Team = apps.get_model('tournament', 'Team')
    women_names = set(NATIONAL_TEAMS_WOMEN) | set(WOMEN_CLUBS)
    Team.objects.filter(name__in=women_names).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0011_populate_teams'),
    ]

    operations = [
        migrations.RunPython(remove_women_teams, noop),
    ]
