# Data migration: fill Team from ea_fc26_teams with default rating 82

from django.db import migrations


def _calculate_tier(rating):
    if rating is None:
        return None
    if 90 <= rating <= 99:
        return 1
    if 80 <= rating <= 89:
        return 2
    if 70 <= rating <= 79:
        return 3
    return None


def populate_teams(apps, schema_editor):
    Team = apps.get_model('tournament', 'Team')
    from tournament.ea_fc26_teams import CLUBS, NATIONAL_TEAMS_MEN, NATIONAL_TEAMS_WOMEN, WOMEN_CLUBS

    seen = set()
    default_rating = 82
    for name in list(CLUBS) + list(NATIONAL_TEAMS_MEN) + list(NATIONAL_TEAMS_WOMEN) + list(WOMEN_CLUBS):
        if name in seen:
            continue
        seen.add(name)
        tier = _calculate_tier(default_rating)
        Team.objects.get_or_create(
            name=name,
            defaults={'rating': default_rating, 'tier': tier},
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0010_team_tournamentteamsettings_assignedteam'),
    ]

    operations = [
        migrations.RunPython(populate_teams, noop),
    ]
