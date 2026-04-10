# -*- coding: utf-8 -*-
"""
Management command: обновить рейтинги в звёздах (клубы и сборные) из онлайн-источника FC 26 Live.
Запуск: python manage.py update_star_ratings
"""
from django.core.management.base import BaseCommand

from tournament.models import Team
from tournament.services.star_ratings_fetcher import fetch_star_ratings_from_web


# Допустимые значения star_rating в БД (30, 35, 40, 45, 50)
VALID_STAR_VALUES = {30, 35, 40, 45, 50}


class Command(BaseCommand):
    help = "Обновить рейтинги в звёздах (3–5 ★) из онлайн-источника FC 26 Live для клубов и сборных."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Не сохранять в БД, только показать, что обновилось бы.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write("Загрузка рейтингов FC 26 Live…")
        ratings = fetch_star_ratings_from_web()
        if not ratings:
            self.stdout.write(self.style.WARNING("Данные с сайта не получены. Рейтинги не изменены."))
            return
        self.stdout.write("Получено записей: %s" % len(ratings))
        updated = 0
        for team in Team.objects.all():
            star = ratings.get(team.name)
            if star is None:
                continue
            if star not in VALID_STAR_VALUES:
                star = min(VALID_STAR_VALUES, key=lambda x: abs(x - star))
            if team.star_rating != star:
                if not dry_run:
                    team.star_rating = star
                    team.save(update_fields=["star_rating"])
                updated += 1
                self.stdout.write("  %s: %s stars" % (team.name, star / 10 if star % 10 == 0 else star / 10))
        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run: обновлено бы записей: %s" % updated))
        else:
            self.stdout.write(self.style.SUCCESS("Обновлено записей: %s" % updated))
