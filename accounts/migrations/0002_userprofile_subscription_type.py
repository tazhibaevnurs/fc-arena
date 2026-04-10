# Generated manually for PRO/FREE subscription type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='subscription_type',
            field=models.CharField(
                choices=[('FREE', 'FREE'), ('PRO', 'PRO')],
                default='FREE',
                max_length=10,
                verbose_name='Тип подписки',
            ),
        ),
    ]
