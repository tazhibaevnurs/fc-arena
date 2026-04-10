# -*- coding: utf-8 -*-
"""
Загрузка рейтингов в звёздах (3–5 ★) из онлайн-источника FC 26 Live.
Клубы: fifagamenews.com/fc-26-team-star-ratings.
Сборные: рейтинги из того же формата при наличии; иначе используются значения из БД (миграция).
"""
import re
import logging

logger = logging.getLogger(__name__)

# Основная страница: клубы (и при наличии — сборные) с рейтингами в звёздах
FC26_STAR_RATINGS_URL = "https://www.fifagamenews.com/fc-26-team-star-ratings/"

# Соответствие названий со страницы нашим названиям в БД (клубы и сборные)
SOURCE_NAME_TO_OUR = {
    "Bayern": "Bayern Munich",
    "OL Lyonnais": "Olympique Lyonnais",
    "OL Lyonnes": "Olympique Lyonnais",
    "Villareal": "Villarreal",
    "SL Benfica": "Benfica",
    "SV Werder Bremen": "Werder Bremen",
    "RC Strasbourg Alsace": "RC Strasbourg",
}


def _parse_star_value(s):
    """'5,0' -> 50, '4,5' -> 45, '3' -> 30."""
    if not s:
        return None
    s = s.strip().replace(",", ".")
    try:
        f = float(s)
        if f <= 0 or f > 5:
            return None
        # 5.0->50, 4.5->45, 4.0->40, 3.5->35, 3.0->30, 2.5->25...
        if f >= 4.75:
            return 50
        if f >= 4.25:
            return 45
        if f >= 3.75:
            return 40
        if f >= 3.25:
            return 35
        if f >= 2.75:
            return 30
        if f >= 2.25:
            return 25
        if f >= 1.75:
            return 20
        if f >= 1.25:
            return 15
        if f >= 0.75:
            return 10
        return 5
    except ValueError:
        return None


def fetch_star_ratings_from_web():
    """
    Загружает страницу с рейтингами FC 26 и возвращает dict { our_team_name: star_30_50 }.
    Только мужские клубы и сборные; женские и дубликаты отбрасываются.
    """
    try:
        import requests
        resp = requests.get(FC26_STAR_RATINGS_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; FC26Arena/1.0)"})
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        logger.warning("Не удалось загрузить рейтинги FC 26: %s", e)
        return {}

    result = {}

    # Вариант 1: HTML-таблица — <tr><td>N</td><td>img?</td><td>Name</td><td>X,Y</td></tr>
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)

    def strip_html(s):
        return re.sub(r"<[^>]+>", "", s).strip()

    for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, re.DOTALL | re.IGNORECASE):
        raw_cells = [m.group(1) for m in td_pattern.finditer(row.group(1))]
        cells = [strip_html(c) for c in raw_cells]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        rating_str = cells[-1].replace(" ", "")
        if not re.match(r"^[\d,\.]+$", rating_str):
            continue
        star = _parse_star_value(cells[-1])
        if star is None:
            continue
        name = None
        for k in range(1, len(cells) - 1):
            c = cells[k]
            if c and len(c) < 80 and not re.match(r"^[\d,\.\s]+$", c.replace(" ", "")):
                name = c
                break
        if not name:
            continue
        name_lower = name.lower()
        if " (w)" in name_lower or " (women)" in name_lower or " women" in name_lower or " femeni" in name_lower or " féminin" in name_lower or " femenino" in name_lower or " vrouwen" in name_lower:
            continue
        our_name = SOURCE_NAME_TO_OUR.get(name, name)
        result[our_name] = star

    return result
