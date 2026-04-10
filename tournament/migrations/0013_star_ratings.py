# Add star rating (3–5 stars, FC 26 Live) to Team and TournamentTeamSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0012_remove_women_teams'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='star_rating',
            field=models.PositiveSmallIntegerField(
                choices=[(30, '3 ★'), (35, '3.5 ★'), (40, '4 ★'), (45, '4.5 ★'), (50, '5 ★')],
                default=40,
                verbose_name='Рейтинг в звёздах',
            ),
        ),
        migrations.AddField(
            model_name='tournamentteamsettings',
            name='min_star_rating',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                choices=[(30, '3 ★'), (35, '3.5 ★'), (40, '4 ★'), (45, '4.5 ★'), (50, '5 ★')],
                verbose_name='Мин. звёзды',
            ),
        ),
        migrations.AddField(
            model_name='tournamentteamsettings',
            name='max_star_rating',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                choices=[(30, '3 ★'), (35, '3.5 ★'), (40, '4 ★'), (45, '4.5 ★'), (50, '5 ★')],
                verbose_name='Макс. звёзды',
            ),
        ),
    ]
