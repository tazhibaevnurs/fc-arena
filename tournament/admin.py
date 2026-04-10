# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from .models import Team, TournamentTeamSettings, Settings, Group, Player, Match, AssignedTeam, AdSettings


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "star_rating_display", "rating", "tier")
    list_filter = ("star_rating",)
    search_fields = ("name",)
    ordering = ("-star_rating", "name")

    @admin.display(description=_("Звёзды"))
    def star_rating_display(self, obj):
        if obj.star_rating is None:
            return "—"
        return "%s ★" % (obj.star_rating / 10 if obj.star_rating % 10 == 0 else obj.star_rating / 10)

    actions = ["update_star_ratings_from_web"]

    @admin.action(description=_("Обновить рейтинги из FC 26 Live (онлайн)"))
    def update_star_ratings_from_web(self, request, queryset):
        from tournament.services.star_ratings_fetcher import fetch_star_ratings_from_web
        ratings = fetch_star_ratings_from_web()
        if not ratings:
            self.message_user(request, _("Не удалось загрузить данные с сайта. Рейтинги не изменены."), level=40)
            return
        valid = {30, 35, 40, 45, 50}
        updated = 0
        for team in Team.objects.all():
            star = ratings.get(team.name)
            if star is None:
                continue
            if star not in valid:
                star = min(valid, key=lambda x: abs(x - star))
            if team.star_rating != star:
                team.star_rating = star
                team.save(update_fields=["star_rating"])
                updated += 1
        self.message_user(request, _("Обновлено записей: %s") % updated)


@admin.register(TournamentTeamSettings)
class TournamentTeamSettingsAdmin(admin.ModelAdmin):
    list_display = ("tournament", "min_star_rating", "max_star_rating", "unique_teams", "draft_mode")
    list_filter = ("unique_teams", "draft_mode", "tier_mode_enabled")


admin.site.register(Settings)
admin.site.register(Group)
admin.site.register(Player)
admin.site.register(Match)
admin.site.register(AssignedTeam)


@admin.register(AdSettings)
class AdSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ads_global_enabled', 'adsense_enabled', 'yandex_ads_enabled')
    fieldsets = (
        (None, {
            'fields': ('ads_global_enabled',),
        }),
        (_('Google AdSense'), {
            'fields': ('adsense_enabled', 'adsense_client_id',
                       'adsense_slot_top', 'adsense_slot_sidebar',
                       'adsense_slot_bottom', 'adsense_slot_in_content'),
        }),
        (_('РСЯ (Яндекс)'), {
            'fields': ('yandex_ads_enabled', 'yandex_block_id'),
        }),
    )

    def has_add_permission(self, request):
        return not AdSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete('fc26_ad_settings')
