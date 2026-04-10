# Generated manually for PRO team generation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0009_alter_group_id_alter_match_id_alter_player_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('rating', models.IntegerField(verbose_name='Рейтинг')),
                ('tier', models.IntegerField(blank=True, null=True, verbose_name='Тир')),
            ],
            options={
                'verbose_name': 'Команда',
                'verbose_name_plural': 'Команды',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TournamentTeamSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_rating', models.IntegerField(blank=True, null=True, verbose_name='Мин. рейтинг')),
                ('max_rating', models.IntegerField(blank=True, null=True, verbose_name='Макс. рейтинг')),
                ('exclude_top_teams', models.BooleanField(default=False, verbose_name='Исключить топ-команды')),
                ('tier_mode_enabled', models.BooleanField(default=False, verbose_name='Режим по тирам')),
                ('unique_teams', models.BooleanField(default=False, verbose_name='Уникальные команды')),
                ('change_each_round', models.BooleanField(default=False, verbose_name='Менять команду каждый раунд')),
                ('draft_mode', models.BooleanField(default=False, verbose_name='Режим драфта')),
                ('tournament', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='team_settings', to='tournament.settings', verbose_name='Турнир')),
            ],
            options={
                'verbose_name': 'Настройки генерации команд',
                'verbose_name_plural': 'Настройки генерации команд',
            },
        ),
        migrations.CreateModel(
            name='AssignedTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_num', models.IntegerField(blank=True, null=True, verbose_name='Раунд (null = на весь турнир)')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='tournament.team', verbose_name='Команда')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_teams', to='tournament.settings', verbose_name='Турнир')),
            ],
            options={
                'verbose_name': 'Назначенная команда',
                'verbose_name_plural': 'Назначенные команды',
                'unique_together': {('tournament', 'team', 'round_num')},
            },
        ),
    ]
