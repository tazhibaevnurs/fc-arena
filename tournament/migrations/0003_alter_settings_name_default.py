# Rename project to FC Arena

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0002_challonge_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='name',
            field=models.CharField(default='FC Arena', max_length=200, verbose_name='Название турнира'),
        ),
    ]
