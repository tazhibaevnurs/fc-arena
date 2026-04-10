from django.db import models
from django.conf import settings
from django.utils import timezone


class GameProfile(models.Model):
    """
    Игровой профиль внутри аккаунта. PRO может иметь несколько, FREE — только один.
    Участвует в турнирах и имеет свою статистику.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_profiles',
        verbose_name='Пользователь',
    )
    nickname = models.CharField(max_length=64, verbose_name='Никнейм')
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Основной профиль',
        help_text='Для FREE всегда один; для PRO — выбранный по умолчанию.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Игровой профиль'
        verbose_name_plural = 'Игровые профили'
        ordering = ['-is_primary', 'created_at']
        unique_together = [('user', 'nickname')]

    def __str__(self):
        return f'{self.nickname} ({self.user.username})'


class ProfileStats(models.Model):
    """Статистика по игровому профилю. Обновляется после каждого сыгранного матча."""
    game_profile = models.OneToOneField(
        GameProfile,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Профиль',
    )
    matches_played = models.PositiveIntegerField(default=0, verbose_name='Матчей сыграно')
    matches_won = models.PositiveIntegerField(default=0, verbose_name='Побед')
    matches_lost = models.PositiveIntegerField(default=0, verbose_name='Поражений')
    matches_draw = models.PositiveIntegerField(default=0, verbose_name='Ничьих')
    tournaments_won = models.PositiveIntegerField(default=0, verbose_name='Турниров выиграно')
    goals_scored = models.PositiveIntegerField(default=0, verbose_name='Голов забито')
    goals_conceded = models.PositiveIntegerField(default=0, verbose_name='Голов пропущено')
    winrate_percent = models.FloatField(default=0.0, verbose_name='Winrate %')
    max_goals_per_match = models.PositiveSmallIntegerField(default=0, verbose_name='Рекорд голов за матч')
    max_goals_conceded_per_match = models.PositiveSmallIntegerField(default=0, verbose_name='Антирекорд пропущенных')
    most_used_team = models.CharField(max_length=200, blank=True, verbose_name='Самая частая команда')

    class Meta:
        verbose_name = 'Статистика профиля'
        verbose_name_plural = 'Статистика профилей'

    def __str__(self):
        return f'Stats: {self.game_profile.nickname}'


class UserProfile(models.Model):
    """Профиль пользователя с подпиской."""
    PLAN_FREE = 'free'
    PLAN_MONTHLY = 'monthly'
    PLAN_YEARLY = 'yearly'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Бесплатный'),
        (PLAN_MONTHLY, 'Месячная ($6/мес)'),
        (PLAN_YEARLY, 'Годовая ($55/год)'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_FREE,
        verbose_name='Тариф',
    )
    subscription_type = models.CharField(
        max_length=10,
        choices=[('FREE', 'FREE'), ('PRO', 'PRO')],
        default='FREE',
        verbose_name='Тип подписки',
    )
    subscription_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Подписка действует до',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.user.username} ({self.get_plan_display()})'

    @property
    def has_active_subscription(self):
        """Есть ли активная платная подписка (без рекламы + история турниров)."""
        if self.plan == self.PLAN_FREE:
            return False
        if not self.subscription_ends_at:
            return False
        return timezone.now() < self.subscription_ends_at

    @property
    def is_pro(self):
        """PRO-функции доступны при активной подписке или явном subscription_type == 'PRO'."""
        return self.subscription_type == 'PRO' or self.has_active_subscription


class PendingSubscriptionPayment(models.Model):
    """Ожидающий платёж подписки (2Checkout или Robokassa). После подтверждения — активация PRO."""
    PROVIDER_2CHECKOUT = '2checkout'
    PROVIDER_ROBOKASSA = 'robokassa'
    PROVIDER_CHOICES = [(PROVIDER_2CHECKOUT, '2Checkout'), (PROVIDER_ROBOKASSA, 'Robokassa')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pending_subscription_payments',
        verbose_name='Пользователь',
    )
    plan = models.CharField(max_length=20, choices=UserProfile.PLAN_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ожидающий платёж подписки'
        verbose_name_plural = 'Ожидающие платежи подписки'
