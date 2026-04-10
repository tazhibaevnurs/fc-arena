# Populate Team.star_rating from FC 26 Live data (ea_fc26_teams.get_team_star_rating)

from django.db import migrations


def populate_star_ratings(apps, schema_editor):
    from tournament.ea_fc26_teams import get_team_star_rating
    Team = apps.get_model('tournament', 'Team')
    for team in Team.objects.all():
        team.star_rating = get_team_star_rating(team.name)
        team.save(update_fields=['star_rating'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0013_star_ratings'),
    ]

    operations = [
        migrations.RunPython(populate_star_ratings, noop),
    ]
