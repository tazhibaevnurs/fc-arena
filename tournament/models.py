from django.db import models
from django.conf import settings as django_settings


def _calculate_tier_from_rating(rating):
    """90–99 → 1, 80–89 → 2, 70–79 → 3, иначе None."""
    if rating is None:
        return None
    if 90 <= rating <= 99:
        return 1
    if 80 <= rating <= 89:
        return 2
    if 70 <= rating <= 79:
        return 3
    return None


# Рейтинг в звёздах: 30=3★, 35=3.5★, 40=4★, 45=4.5★, 50=5★ (FC 26 Live)
STAR_RATING_CHOICES = [(30, '3 ★'), (35, '3.5 ★'), (40, '4 ★'), (45, '4.5 ★'), (50, '5 ★')]


class Team(models.Model):
    """Команда FC 26 с рейтингом для PRO-генерации."""
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    rating = models.IntegerField(verbose_name='Рейтинг (числовой)')
    star_rating = models.PositiveSmallIntegerField(
        verbose_name='Рейтинг в звёздах',
        choices=STAR_RATING_CHOICES,
        default=40,
    )
    tier = models.IntegerField(null=True, blank=True, verbose_name='Тир')

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rating})"

    def save(self, *args, **kwargs):
        self.tier = _calculate_tier_from_rating(self.rating)
        super().save(*args, **kwargs)

    @classmethod
    def calculate_tier(cls, rating):
        return _calculate_tier_from_rating(rating)


class Settings(models.Model):
    """Tournament settings (Challonge-style: name, description). Один экземпляр = один турнир."""
    TOURNAMENT_ROUND_ROBIN = 'round_robin'
    TOURNAMENT_BRACKET = 'bracket'
    TOURNAMENT_TYPES = [
        (TOURNAMENT_ROUND_ROBIN, 'Круговой'),
        (TOURNAMENT_BRACKET, 'Олимпийская система (брекеты)'),
    ]
    name = models.CharField(max_length=200, default='FC Arena', verbose_name='Название турнира')
    description = models.TextField(blank=True, verbose_name='Описание / объявления')
    tournament_type = models.CharField(
        max_length=20, choices=TOURNAMENT_TYPES, default=TOURNAMENT_ROUND_ROBIN,
        verbose_name='Тип турнира'
    )
    is_double_round = models.BooleanField(default=False, verbose_name='Два круга')
    has_group_stage = models.BooleanField(default=False, verbose_name='С групповым этапом')
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tournaments',
        verbose_name='Владелец',
    )

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'
        ordering = ['-created_at']


class TournamentTeamSettings(models.Model):
    """PRO: настройки генерации команд для турнира."""
    tournament = models.OneToOneField(
        Settings,
        on_delete=models.CASCADE,
        related_name='team_settings',
        verbose_name='Турнир',
    )
    min_rating = models.IntegerField(null=True, blank=True, verbose_name='Мин. рейтинг (числовой)')
    max_rating = models.IntegerField(null=True, blank=True, verbose_name='Макс. рейтинг (числовой)')
    min_star_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=STAR_RATING_CHOICES,
        verbose_name='Мин. звёзды',
    )
    max_star_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=STAR_RATING_CHOICES,
        verbose_name='Макс. звёзды',
    )
    exclude_top_teams = models.BooleanField(default=False, verbose_name='Исключить топ-команды')
    tier_mode_enabled = models.BooleanField(default=False, verbose_name='Режим по тирам')
    unique_teams = models.BooleanField(default=False, verbose_name='Уникальные команды')
    change_each_round = models.BooleanField(default=False, verbose_name='Менять команду каждый раунд')
    draft_mode = models.BooleanField(default=False, verbose_name='Режим драфта')

    class Meta:
        verbose_name = 'Настройки генерации команд'
        verbose_name_plural = 'Настройки генерации команд'


class AssignedTeam(models.Model):
    """PRO: какая команда назначена турниру/раунду (для unique_teams и change_each_round)."""
    tournament = models.ForeignKey(
        Settings,
        on_delete=models.CASCADE,
        related_name='assigned_teams',
        verbose_name='Турнир',
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Команда',
    )
    round_num = models.IntegerField(null=True, blank=True, verbose_name='Раунд (null = на весь турнир)')

    class Meta:
        verbose_name = 'Назначенная команда'
        verbose_name_plural = 'Назначенные команды'
        unique_together = [('tournament', 'team', 'round_num')]


class Group(models.Model):
    """Группа в турнире (для группового этапа: по 4 команды)."""
    settings = models.ForeignKey(
        Settings,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='groups',
        verbose_name='Турнир',
    )
    name = models.CharField(max_length=50, verbose_name='Название группы')
    order = models.PositiveSmallIntegerField(default=1, verbose_name='Порядок (A=1, B=2, …)')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['order']

    def __str__(self):
        return self.name


class Player(models.Model):
    """Player/Team in tournament (Challonge-style: seed for tie-break). Может быть привязан к GameProfile (PRO)."""
    settings = models.ForeignKey(
        Settings,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='players',
        verbose_name='Турнир',
    )
    game_profile = models.ForeignKey(
        'accounts.GameProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tournament_players',
        verbose_name='Игровой профиль',
    )
    name = models.CharField(max_length=100, blank=True, verbose_name='Имя игрока')
    team_name = models.CharField(max_length=100, verbose_name='Название команды')
    color = models.CharField(max_length=20, default='#ef4444')
    seed = models.PositiveSmallIntegerField(default=1, verbose_name='Посев')
    logo_url = models.URLField(max_length=500, blank=True, verbose_name='URL логотипа')
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='players',
        verbose_name='Группа',
    )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return f"{self.name} ({self.team_name})"


class Match(models.Model):
    """Match between two players (round-robin or bracket)"""
    settings = models.ForeignKey(
        Settings,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='matches',
        verbose_name='Турнир',
    )
    round_num = models.IntegerField(default=1, verbose_name='Номер тура / раунда')
    home_player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='home_matches',
        verbose_name='Хозяин',
        null=True,
        blank=True,
    )
    away_player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='away_matches',
        verbose_name='Гость',
        null=True,
        blank=True,
    )
    # Брекет: куда переходит победитель (следующий матч и слот)
    next_match = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prev_matches',
        verbose_name='Следующий матч для победителя',
    )
    winner_slot = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Слот победителя (home/away)',
        help_text='В какую ячейку следующего матча записать победителя',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches',
        verbose_name='Группа (для группового этапа)',
    )
    home_score = models.IntegerField(null=True, blank=True, verbose_name='Голы хозяина')
    away_score = models.IntegerField(null=True, blank=True, verbose_name='Голы гостя')
    is_played = models.BooleanField(default=False, verbose_name='Сыгран')
    is_home = models.BooleanField(default=True, verbose_name='Первый матч дома')
    station = models.CharField(max_length=100, blank=True, verbose_name='Корт / станция')
    notes = models.TextField(blank=True, verbose_name='Заметки к матчу')

    class Meta:
        verbose_name = 'Матч'
        verbose_name_plural = 'Матчи'
        ordering = ['round_num', 'id']

    def __str__(self):
        return f"Тур {self.round_num}: {self.home_player} vs {self.away_player}"

    @property
    def winner(self):
        if not self.is_played:
            return None
        if self.home_score > self.away_score:
            return self.home_player
        elif self.away_score > self.home_score:
            return self.away_player
        return None  # Draw


def _default_highlight_slug():
    import uuid
    return uuid.uuid4().hex[:16]


class MatchHighlight(models.Model):
    """PRO: публичная ссылка на матч (без авторизации)."""
    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name='highlight',
        verbose_name='Матч',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        default=_default_highlight_slug,
        verbose_name='Код ссылки',
    )
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_highlights',
        verbose_name='Кто создал',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Публичная ссылка на матч'
        verbose_name_plural = 'Публичные ссылки на матчи'

    def __str__(self):
        return f'Match {self.match_id} ({self.slug})'


class TournamentHighlight(models.Model):
    """PRO: публичная страница турнира."""
    tournament = models.OneToOneField(
        Settings,
        on_delete=models.CASCADE,
        related_name='highlight',
        verbose_name='Турнир',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        default=_default_highlight_slug,
        verbose_name='Код ссылки',
    )
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournament_highlights',
        verbose_name='Кто создал',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Публичная страница турнира'
        verbose_name_plural = 'Публичные страницы турниров'

    def __str__(self):
        return f'Tournament {self.tournament_id} ({self.slug})'


class AdSettings(models.Model):
    """Глобальные настройки рекламы (синглтон, id=1). Включение/выключение AdSense и РСЯ через админку."""
    ads_global_enabled = models.BooleanField(default=True, verbose_name='Реклама включена')
    # AdSense
    adsense_enabled = models.BooleanField(default=False, verbose_name='Включить Google AdSense')
    adsense_client_id = models.CharField(max_length=64, blank=True, verbose_name='AdSense client id (ca-pub-...)')
    adsense_slot_top = models.CharField(max_length=32, blank=True, verbose_name='AdSense слот: верх (leaderboard)')
    adsense_slot_sidebar = models.CharField(max_length=32, blank=True, verbose_name='AdSense слот: боковая панель')
    adsense_slot_bottom = models.CharField(max_length=32, blank=True, verbose_name='AdSense слот: низ')
    adsense_slot_in_content = models.CharField(max_length=32, blank=True, verbose_name='AdSense слот: в контенте')
    # РСЯ (Яндекс)
    yandex_ads_enabled = models.BooleanField(default=False, verbose_name='Включить РСЯ (Яндекс)')
    yandex_block_id = models.CharField(max_length=64, blank=True, verbose_name='РСЯ: ID блока (R-A-...)')

    class Meta:
        verbose_name = 'Настройки рекламы'
        verbose_name_plural = 'Настройки рекламы'

    def __str__(self):
        return 'Настройки рекламы'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'ads_global_enabled': True})
        return obj
