# -*- coding: utf-8 -*-
"""
Генератор футбольных клубов и сборных из EA Sports FC 26.
Данные на основе официального списка лиг и команд в игре.
"""
import random


# Клубы EA Sports FC 26 (топ-лиги и популярные команды)
CLUBS = [
    # Premier League
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool", "Manchester City",
    "Manchester United", "Newcastle United", "Nottingham Forest", "Tottenham",
    "West Ham", "Wolverhampton",
    # La Liga
    "Alavés", "Athletic Bilbao", "Atlético Madrid", "Celta Vigo", "Espanyol",
    "FC Barcelona", "Getafe", "Girona", "Mallorca", "Osasuna", "Rayo Vallecano",
    "Real Betis", "Real Madrid", "Real Sociedad", "Sevilla", "Valencia", "Villarreal",
    # Serie A
    "Bologna", "Fiorentina", "Genoa", "Juventus", "Lazio", "Milan", "Napoli",
    "AS Roma", "Inter", "Atalanta", "Torino", "Udinese",
    # Bundesliga
    "Bayern Munich", "Borussia Dortmund", "Bayer Leverkusen", "RB Leipzig",
    "Eintracht Frankfurt", "VfL Wolfsburg", "VfB Stuttgart", "1899 Hoffenheim",
    "Borussia Mönchengladbach", "Werder Bremen", "SC Freiburg", "Union Berlin",
    # Ligue 1
    "Paris Saint-Germain", "Olympique de Marseille", "Olympique Lyonnais",
    "AS Monaco", "LOSC Lille", "Stade Rennais FC", "OGC Nice", "RC Strasbourg",
    "Stade Brestois 29", "Toulouse FC",
    # Другие лиги
    "Benfica", "FC Porto", "Sporting", "Ajax", "PSV", "Feyenoord",
    "Celtic", "Rangers", "Club Brugge", "Anderlecht",
    "Boca Juniors", "River Plate", "Independiente", "Racing Club", "San Lorenzo",
    "Atlanta United", "LA Galaxy", "Inter Miami CF", "Seattle Sounders FC",
    "Toronto FC", "CF Montréal", "Cruz Azul", "America", "Guadalajara", "Monterrey",
    "Al Hilal", "Al Nassr", "Al Ittihad", "Zenit", "Shakhtar Donetsk",
]

# Сборные (мужские) EA Sports FC 26 — полностью лицензированные
NATIONAL_TEAMS_MEN = [
    "Argentina", "Brazil", "Canada", "China", "Croatia", "Czechia", "Denmark",
    "England", "Finland", "France", "Germany", "Ghana", "Hungary", "Iceland",
    "Italy", "Mexico", "Morocco", "Netherlands", "Northern Ireland", "Norway",
    "Poland", "Portugal", "Qatar", "Republic of Ireland", "Romania", "Scotland",
    "Spain", "Sweden", "Ukraine", "United States", "Wales",
]

# Сборные (женские) EA Sports FC 26
NATIONAL_TEAMS_WOMEN = [
    "Argentina", "Brazil", "Canada", "China", "Denmark", "England", "Finland",
    "France", "Germany", "Iceland", "Mexico", "Netherlands", "Norway", "Poland",
    "Portugal", "Scotland", "Spain", "Sweden", "United States",
]

# Женские клубы EA Sports FC 26 (топ-лиги и популярные команды)
WOMEN_CLUBS = [
    # Англия
    "Arsenal WFC", "Chelsea FC Women", "Manchester City WFC", "Manchester United Women",
    "Liverpool FC Women", "Tottenham Hotspur Women", "Everton Women", "Aston Villa Women",
    "Brighton & Hove Albion Women", "West Ham United Women",
    # Испания
    "FC Barcelona Femení", "Real Madrid Femenino", "Atlético Madrid Femenino",
    "Levante UD Femenino", "Real Sociedad Femenino", "Sevilla FC Women",
    # Франция
    "Olympique Lyonnais Féminin", "Paris Saint-Germain Féminines", "Paris FC (women)",
    # Германия
    "Bayern Munich Women", "VfL Wolfsburg Women", "Eintracht Frankfurt Women",
    "RB Leipzig Women", "Bayer Leverkusen Women",
    # Италия
    "Juventus Women", "AS Roma Women", "AC Milan Women", "Inter Milano Women",
    "Fiorentina Women", "Napoli Women",
    # Нидерланды, Португалия, Шотландия
    "Ajax Vrouwen", "PSV Vrouwen", "Benfica Women", "Sporting CP Women",
    "Celtic FC Women", "Rangers WFC",
]

# Рейтинг в звёздах FC 26 Live (источник: fifagamenews.com/fc-26-team-star-ratings)
# Значения: 30=3★, 35=3.5★, 40=4★, 45=4.5★, 50=5★. Только мужские клубы и сборные.
TEAM_STAR_RATINGS = {
    # 5★
    "Paris Saint-Germain": 50, "FC Barcelona": 50, "Real Madrid": 50, "Arsenal": 50,
    "Liverpool": 50, "Manchester City": 50, "Bayern Munich": 50, "Inter": 50,
    # 4.5★
    "Atlético Madrid": 45, "Chelsea": 45, "Newcastle United": 45, "Tottenham": 45,
    "Borussia Dortmund": 45, "Napoli": 45, "Aston Villa": 45, "Manchester United": 45,
    "Bayer Leverkusen": 45, "RB Leipzig": 45, "Juventus": 45, "Milan": 45,
    "Nottingham Forest": 45, "AS Roma": 45, "Atalanta": 45, "Lazio": 45,
    "Sporting": 45, "Athletic Bilbao": 45,
    # 4★
    "Bournemouth": 40, "Brighton & Hove Albion": 40, "Crystal Palace": 40, "West Ham": 40,
    "AS Monaco": 40, "Olympique de Marseille": 40, "Eintracht Frankfurt": 40,
    "Benfica": 40, "Real Betis": 40, "Real Sociedad": 40, "Sevilla": 40, "Valencia": 40,
    "Villarreal": 40, "Brentford": 40, "Fulham": 40, "LOSC Lille": 40, "VfB Stuttgart": 40,
    "VfL Wolfsburg": 40, "Bologna": 40, "Fiorentina": 40, "Girona": 40, "Mallorca": 40,
    "Rayo Vallecano": 40, "Everton": 40, "Wolverhampton": 40, "OGC Nice": 40,
    "Olympique Lyonnais": 40, "Stade Rennais FC": 40, "Borussia Mönchengladbach": 40,
    "SC Freiburg": 40, "Union Berlin": 40, "Torino": 40, "PSV": 40, "FC Porto": 40,
    "Al Hilal": 40, "Al Nassr": 40, "Celta Vigo": 40, "Getafe": 40, "Osasuna": 40,
    "1899 Hoffenheim": 40, "Ajax": 40, "Feyenoord": 40, "Celtic": 40,
    "Boca Juniors": 40, "River Plate": 40, "Al Ittihad": 40, "Zenit": 30, "Shakhtar Donetsk": 30,
    "Independiente": 35, "Racing Club": 35, "San Lorenzo": 30,
    "Atlanta United": 30, "LA Galaxy": 30, "Inter Miami CF": 35, "Seattle Sounders FC": 35,
    "Toronto FC": 30, "CF Montréal": 30, "Cruz Azul": 40, "America": 40,
    "Guadalajara": 40, "Monterrey": 40, "Alavés": 35, "Espanyol": 35,
    "Genoa": 35, "Udinese": 35, "Rangers": 35, "Club Brugge": 35, "Anderlecht": 35,
    "Stade Brestois 29": 35, "Toulouse FC": 35, "RC Strasbourg": 40,
}
# Сборные: рейтинг в звёздах (тот же фильтр 3–5 ★, что и для клубов)
# Все мужские сборные из NATIONAL_TEAMS_MEN; при онлайн-обновлении перезаписываются.
NATIONAL_STAR_RATINGS = {
    "Argentina": 50, "Brazil": 50, "France": 50, "Germany": 50, "Spain": 50,
    "Italy": 50, "England": 50, "Portugal": 45, "Netherlands": 45, "Croatia": 45,
    "Morocco": 45, "United States": 45, "Mexico": 45, "Denmark": 45, "Poland": 45,
    "Ukraine": 45, "Scotland": 45, "Wales": 45, "Sweden": 40, "Czechia": 40,
    "Hungary": 40, "Romania": 40, "Norway": 40, "Republic of Ireland": 40,
    "Northern Ireland": 40, "Ghana": 40, "Canada": 40, "China": 40, "Qatar": 40,
    "Finland": 40, "Iceland": 40,
}


def get_team_star_rating(team_name: str) -> int:
    """Возвращает рейтинг в звёздах (30–50) для команды. 40 = 4★ по умолчанию."""
    if not team_name:
        return 40
    name = team_name.strip()
    if name in TEAM_STAR_RATINGS:
        return TEAM_STAR_RATINGS[name]
    if name in NATIONAL_STAR_RATINGS:
        return NATIONAL_STAR_RATINGS[name]
    return 40


# Для логотипа женского клуба используем эмблему мужского (если есть)
_WOMEN_CLUB_LOGO_ALIAS = {
    "Arsenal WFC": "Arsenal", "Chelsea FC Women": "Chelsea", "Manchester City WFC": "Manchester City",
    "Manchester United Women": "Manchester United", "Liverpool FC Women": "Liverpool",
    "Tottenham Hotspur Women": "Tottenham", "Everton Women": "Everton", "Aston Villa Women": "Aston Villa",
    "Brighton & Hove Albion Women": "Brighton & Hove Albion", "West Ham United Women": "West Ham",
    "FC Barcelona Femení": "FC Barcelona", "Real Madrid Femenino": "Real Madrid",
    "Atlético Madrid Femenino": "Atlético Madrid", "Real Sociedad Femenino": "Real Sociedad",
    "Sevilla FC Women": "Sevilla", "Olympique Lyonnais Féminin": "Olympique Lyonnais",
    "Paris Saint-Germain Féminines": "Paris Saint-Germain", "Bayern Munich Women": "Bayern Munich",
    "VfL Wolfsburg Women": "VfL Wolfsburg", "Eintracht Frankfurt Women": "Eintracht Frankfurt",
    "RB Leipzig Women": "RB Leipzig", "Bayer Leverkusen Women": "Bayer Leverkusen",
    "Juventus Women": "Juventus", "AS Roma Women": "AS Roma", "AC Milan Women": "Milan",
    "Inter Milano Women": "Inter", "Fiorentina Women": "Fiorentina", "Napoli Women": "Napoli",
    "Ajax Vrouwen": "Ajax", "PSV Vrouwen": "PSV", "Benfica Women": "Benfica",
    "Sporting CP Women": "Sporting", "Celtic FC Women": "Celtic", "Rangers WFC": "Rangers",
}


def get_random_clubs(count: int, unique: bool = True) -> list[dict]:
    """
    Возвращает список из `count` случайных клубов EA FC 26.
    Каждый элемент — словарь {"name": "...", "team_name": "..."}.
    """
    pool = list(CLUBS)
    if unique and count > len(pool):
        count = len(pool)
    if unique:
        chosen = random.sample(pool, min(count, len(pool)))
    else:
        chosen = random.choices(pool, k=count)
    # Генератор заполняет только название команды, имя игрока — пустое
    return [{"name": "", "team_name": c, "logo_url": get_logo_url(c)} for c in chosen]


def get_random_national_teams(count: int, women: bool = False, unique: bool = True) -> list[dict]:
    """
    Возвращает список из `count` случайных сборных EA FC 26.
    women=True — женские сборные, иначе мужские.
    Заполняется только team_name и logo_url, name — пустое.
    """
    pool = NATIONAL_TEAMS_WOMEN if women else NATIONAL_TEAMS_MEN
    if unique and count > len(pool):
        count = len(pool)
    if unique:
        chosen = random.sample(pool, min(count, len(pool)))
    else:
        chosen = random.choices(pool, k=count)
    return [{"name": "", "team_name": c, "logo_url": get_logo_url(c)} for c in chosen]


def get_random_women_clubs(count: int, unique: bool = True) -> list[dict]:
    """
    Возвращает список из `count` случайных женских клубов EA FC 26.
    Логотип подставляется от соответствующего мужского клуба (если есть).
    """
    pool = list(WOMEN_CLUBS)
    if unique and count > len(pool):
        count = len(pool)
    if unique:
        chosen = random.sample(pool, min(count, len(pool)))
    else:
        chosen = random.choices(pool, k=count)
    return [{"name": "", "team_name": c, "logo_url": get_logo_url(c)} for c in chosen]


# ID команд football-data.org для эмблем (crests.football-data.org/{id}.png)
_CLUB_CREST_IDS = {
    # Premier League
    "Arsenal": 57,
    "Aston Villa": 58,
    "Bournemouth": 1045,
    "Brentford": 402,
    "Brighton & Hove Albion": 397,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Liverpool": 64,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Tottenham": 73,
    "West Ham": 563,
    "Wolverhampton": 76,
    # La Liga
    "Alavés": 263,
    "Athletic Bilbao": 77,
    "Atlético Madrid": 78,
    "Celta Vigo": 558,
    "Espanyol": 80,
    "FC Barcelona": 81,
    "Getafe": 82,
    "Girona": 530,
    "Mallorca": 79,
    "Osasuna": 83,
    "Rayo Vallecano": 87,
    "Real Betis": 90,
    "Real Madrid": 86,
    "Real Sociedad": 92,
    "Sevilla": 559,
    "Valencia": 95,
    "Villarreal": 94,
    # Serie A
    "Bologna": 103,
    "Fiorentina": 99,
    "Genoa": 107,
    "Juventus": 109,
    "Lazio": 110,
    "Milan": 98,
    "Napoli": 113,
    "AS Roma": 100,
    "Inter": 108,
    "Atalanta": 102,
    "Torino": 505,
    "Udinese": 115,
    # Bundesliga
    "Bayern Munich": 5,
    "Borussia Dortmund": 4,
    # "Bayer Leverkusen": 6 — в API это Schalke 04; логотип Bayer в _CLUB_LOGO_DIRECT_URLS
    "RB Leipzig": 721,
    "Eintracht Frankfurt": 19,
    "VfL Wolfsburg": 11,
    "VfB Stuttgart": 10,
    "1899 Hoffenheim": 2,
    "Borussia Mönchengladbach": 18,
    "Werder Bremen": 12,
    "SC Freiburg": 17,
    "Union Berlin": 28,
    # Ligue 1
    "Paris Saint-Germain": 524,
    "Olympique de Marseille": 516,
    "Olympique Lyonnais": 104,
    "AS Monaco": 548,
    "LOSC Lille": 521,
    "Stade Rennais FC": 529,
    "OGC Nice": 522,
    "RC Strasbourg": 574,
    "Stade Brestois 29": 532,
    "Toulouse FC": 511,
    # Другие лиги
    "Benfica": 190,
    "FC Porto": 503,
    "Sporting": 498,
    "Ajax": 678,
    "PSV": 674,
    "Feyenoord": 675,
    "Celtic": 1085,
    "Rangers": 1082,
    "Club Brugge": 728,
    "Anderlecht": 729,
    "Boca Juniors": 2061,
    "River Plate": 2062,
    "Independiente": 2063,
    "Racing Club": 2064,
    "San Lorenzo": 2072,
    "Atlanta United": 2082,
    "LA Galaxy": 357,
    "Inter Miami CF": 2114,
    "Seattle Sounders FC": 2115,
    "CF Montréal": 2084,
    "Cruz Azul": 581,
    "America": 579,
    "Guadalajara": 578,
    "Monterrey": 580,
    "Zenit": 731,
    "Shakhtar Donetsk": 1887,
}

# Проверенные прямые URL логотипов (Wikimedia Commons и др.). Приоритет над crests — чтобы не показывать чужие/битые эмблемы.
_CLUB_LOGO_DIRECT_URLS = {
    # Саудовские клубы (в API нет эмблем)
    "Al Hilal": "https://upload.wikimedia.org/wikipedia/commons/2/22/Al-Hilal-Logo.png",
    "Al Nassr": "https://upload.wikimedia.org/wikipedia/commons/c/c1/Al_nasr_logo.png",
    "Al Ittihad": "https://upload.wikimedia.org/wikipedia/commons/c/cf/Al-Ittihad_logo.png",
    # Шотландия (crests 404)
    "Celtic": "https://upload.wikimedia.org/wikipedia/sco/a/a8/Celtic_FC.png",
    "Rangers": "https://upload.wikimedia.org/wikipedia/en/8/8d/StarScrollCrestRangersFC.svg",
    # Бельгия
    "Anderlecht": "https://upload.wikimedia.org/wikipedia/commons/7/70/RSC_Anderlecht_Logo_1908-1933.png",
    # MLS (Toronto — ID в API отдавал лого Racing)
    "Toronto FC": "https://upload.wikimedia.org/wikipedia/commons/d/dc/MLS_crest_logo_RGB_-_Toronto_FC.svg",
    # Россия / Украина
    "Zenit": "https://upload.wikimedia.org/wikipedia/commons/e/ef/FK_Zenit_St_Peterburg.svg",
    "Shakhtar Donetsk": "https://upload.wikimedia.org/wikibooks/en/7/79/Shakhtar_Donetsk_Logo.jpg",
    # Нидерланды (проверенные Commons)
    "Feyenoord": "https://upload.wikimedia.org/wikipedia/commons/f/f9/Feyenoord_logo_since_2024.svg",
    # Аргентина (проверенные Commons)
    "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Boca_Juniors_logo18.svg",
    "River Plate": "https://upload.wikimedia.org/wikipedia/commons/4/43/Club_Atl%C3%A9tico_River_Plate_logo.svg",
    # Бундеслига: ID 6 в football-data = Schalke 04, не Bayer Leverkusen — используем прямой URL
    "Bayer Leverkusen": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Logo_TSV_Bayer_04_Leverkusen.svg",
}

# ISO 2 коды стран для флагов (flagcdn.com)
_COUNTRY_ISO = {
    "Argentina": "ar", "Brazil": "br", "Canada": "ca", "China": "cn", "Croatia": "hr",
    "Czechia": "cz", "Denmark": "dk", "England": "gb-eng", "Finland": "fi", "France": "fr",
    "Germany": "de", "Ghana": "gh", "Hungary": "hu", "Iceland": "is", "Italy": "it",
    "Mexico": "mx", "Morocco": "ma", "Netherlands": "nl", "Northern Ireland": "gb-nir",
    "Norway": "no", "Poland": "pl", "Portugal": "pt", "Qatar": "qa",
    "Republic of Ireland": "ie", "Romania": "ro", "Scotland": "gb-sct", "Spain": "es",
    "Sweden": "se", "Ukraine": "ua", "United States": "us", "Wales": "gb-wls",
}


def get_logo_url(team_name: str) -> str:
    """
    Возвращает URL логотипа/флага для команды.
    Сборные — флаг с flagcdn.com; клубы — эмблема. Для женских клубов используется логотип мужского.
    """
    if not team_name:
        return ""
    name = team_name.strip()
    name_for_logo = _WOMEN_CLUB_LOGO_ALIAS.get(name, name)
    # Сборные: флаг страны
    iso = _COUNTRY_ISO.get(name_for_logo)
    if iso:
        return f"https://flagcdn.com/w40/{iso}.png"
    # Клубы с прямым URL (напр. саудовские — Wikimedia)
    direct = _CLUB_LOGO_DIRECT_URLS.get(name_for_logo)
    if direct:
        return direct
    # Остальные клубы: эмблема football-data.org
    crest_id = _CLUB_CREST_IDS.get(name_for_logo)
    if crest_id is not None:
        return f"https://crests.football-data.org/{crest_id}.png"
    return ""


def get_all_clubs() -> list[str]:
    """Возвращает полный список клубов (названия)."""
    return list(CLUBS)


def get_all_national_teams(men: bool = True, women: bool = True) -> list[str]:
    """Возвращает список всех сборных. По умолчанию мужские и женские без дублей."""
    result = set()
    if men:
        result.update(NATIONAL_TEAMS_MEN)
    if women:
        result.update(NATIONAL_TEAMS_WOMEN)
    return sorted(result)


def _normalize(s: str) -> str:
    """Нормализация для поиска: нижний регистр, без лишних пробелов."""
    return " ".join((s or "").lower().split())


# Алиасы для автодополнения: вариант названия (нормализованный) -> каноническое имя (как в CLUBS/NATIONAL)
# Кириллица, латиница, разные языки — при вводе "Барселона" подставится FC Barcelona с логотипом.
TEAM_ALIASES = {
    # Барселона
    "барселона": "FC Barcelona", "barcelona": "FC Barcelona", "барса": "FC Barcelona",
    # Реал Мадрид
    "реал мадрид": "Real Madrid", "real madrid": "Real Madrid", "реал": "Real Madrid",
    "мадрид": "Real Madrid", "madrid": "Real Madrid",
    # АПЛ
    "арсенал": "Arsenal", "arsenal": "Arsenal",
    "челси": "Chelsea", "chelsea": "Chelsea",
    "ливерпуль": "Liverpool", "liverpool": "Liverpool",
    "манчестер сити": "Manchester City", "manchester city": "Manchester City", "сити": "Manchester City", "city": "Manchester City",
    "манчестер юнайтед": "Manchester United", "manchester united": "Manchester United", "юнайтед": "Manchester United", "united": "Manchester United",
    "тоттенхэм": "Tottenham", "tottenham": "Tottenham", "спурс": "Tottenham", "spurs": "Tottenham",
    "астон вилла": "Aston Villa", "aston villa": "Aston Villa", "вилла": "Aston Villa", "villa": "Aston Villa",
    "ньюкасл": "Newcastle United", "newcastle": "Newcastle United", "newcastle united": "Newcastle United",
    "вест хэм": "West Ham", "west ham": "West Ham",
    "вулверхэмптон": "Wolverhampton", "wolverhampton": "Wolverhampton", "волки": "Wolverhampton", "wolves": "Wolverhampton",
    "эвертон": "Everton", "everton": "Everton",
    "фулхэм": "Fulham", "fulham": "Fulham",
    "кристал пэлас": "Crystal Palace", "crystal palace": "Crystal Palace", "пэлас": "Crystal Palace", "palace": "Crystal Palace",
    "брайтон": "Brighton & Hove Albion", "brighton": "Brighton & Hove Albion",
    "брентфорд": "Brentford", "brentford": "Brentford",
    "бурнмут": "Bournemouth", "bournemouth": "Bournemouth",
    "ноттингем форест": "Nottingham Forest", "nottingham forest": "Nottingham Forest", "форест": "Nottingham Forest", "forest": "Nottingham Forest",
    # Ла Лига
    "атлетико": "Atlético Madrid", "atletico": "Atlético Madrid", "атлетико мадрид": "Atlético Madrid", "atletico madrid": "Atlético Madrid",
    "севилья": "Sevilla", "sevilla": "Sevilla",
    "валенсия": "Valencia", "valencia": "Valencia",
    "реал сосьедад": "Real Sociedad", "real sociedad": "Real Sociedad", "сосьедад": "Real Sociedad", "sociedad": "Real Sociedad",
    "реал бетис": "Real Betis", "real betis": "Real Betis", "бетис": "Real Betis", "betis": "Real Betis",
    "вильярреал": "Villarreal", "villarreal": "Villarreal",
    "аталетик бильбао": "Athletic Bilbao", "athletic bilbao": "Athletic Bilbao", "бильбао": "Athletic Bilbao", "bilbao": "Athletic Bilbao",
    "хеетафе": "Getafe", "getafe": "Getafe",
    "хеirona": "Girona", "girona": "Girona", "жирона": "Girona",
    "сельта": "Celta Vigo", "celta vigo": "Celta Vigo", "celta": "Celta Vigo",
    "майорка": "Mallorca", "mallorca": "Mallorca",
    "осасуна": "Osasuna", "osasuna": "Osasuna",
    "райо вальекано": "Rayo Vallecano", "rayo vallecano": "Rayo Vallecano", "райо": "Rayo Vallecano", "rayo": "Rayo Vallecano",
    "алавес": "Alavés", "alaves": "Alavés", "alavés": "Alavés",
    "эспаньол": "Espanyol", "espanyol": "Espanyol",
    # Серия А
    "ювентус": "Juventus", "juventus": "Juventus", "юве": "Juventus", "juve": "Juventus",
    "интер": "Inter", "inter": "Inter", "интернационале": "Inter", "internazionale": "Inter",
    "милан": "Milan", "milan": "Milan", "ак милан": "Milan", "ac milan": "Milan",
    "рома": "AS Roma", "roma": "AS Roma", "as roma": "AS Roma",
    "лацио": "Lazio", "lazio": "Lazio",
    "наполи": "Napoli", "napoli": "Napoli",
    "аталанта": "Atalanta", "atalanta": "Atalanta",
    "фиорентина": "Fiorentina", "fiorentina": "Fiorentina", "фиоре": "Fiorentina", "viola": "Fiorentina",
    "болонья": "Bologna", "bologna": "Bologna",
    "торино": "Torino", "torino": "Torino",
    "дженоа": "Genoa", "genoa": "Genoa",
    "удинезе": "Udinese", "udinese": "Udinese",
    # Бундеслига
    "бавария": "Bayern Munich", "bayern": "Bayern Munich", "bayern munich": "Bayern Munich", "баварья": "Bayern Munich",
    "боруссия дортмунд": "Borussia Dortmund", "borussia dortmund": "Borussia Dortmund", "дортмунд": "Borussia Dortmund", "dortmund": "Borussia Dortmund", "бву": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "байер леверкузен": "Bayer Leverkusen", "bayer leverkusen": "Bayer Leverkusen", "леверкузен": "Bayer Leverkusen", "leverkusen": "Bayer Leverkusen",
    "рб лейпциг": "RB Leipzig", "rb leipzig": "RB Leipzig", "лейпциг": "RB Leipzig", "leipzig": "RB Leipzig",
    "айнтрахт франкфурт": "Eintracht Frankfurt", "eintracht frankfurt": "Eintracht Frankfurt", "франкфурт": "Eintracht Frankfurt", "frankfurt": "Eintracht Frankfurt",
    "вольфсбург": "VfL Wolfsburg", "wolfsburg": "VfL Wolfsburg", "vfl wolfsburg": "VfL Wolfsburg",
    "штутгарт": "VfB Stuttgart", "stuttgart": "VfB Stuttgart", "vfb stuttgart": "VfB Stuttgart",
    "хоффенхайм": "1899 Hoffenheim", "hoffenheim": "1899 Hoffenheim",
    "боруссия мёнхенгладбах": "Borussia Mönchengladbach", "gladbach": "Borussia Mönchengladbach", "мёнхенгладбах": "Borussia Mönchengladbach",
    "вердер": "Werder Bremen", "werder bremen": "Werder Bremen", "bremen": "Werder Bremen", "бремен": "Werder Bremen",
    "фрайбург": "SC Freiburg", "freiburg": "SC Freiburg", "sc freiburg": "SC Freiburg",
    "унион берлин": "Union Berlin", "union berlin": "Union Berlin",
    # Лига 1
    "псж": "Paris Saint-Germain", "psg": "Paris Saint-Germain", "пари сен-жермен": "Paris Saint-Germain", "paris saint-germain": "Paris Saint-Germain", "париж": "Paris Saint-Germain", "paris": "Paris Saint-Germain",
    "марсель": "Olympique de Marseille", "marseille": "Olympique de Marseille", "olympique marseille": "Olympique de Marseille",
    "лион": "Olympique Lyonnais", "lyon": "Olympique Lyonnais", "олимпник лион": "Olympique Lyonnais", "olympique lyonnais": "Olympique Lyonnais",
    "монако": "AS Monaco", "monaco": "AS Monaco", "as monaco": "AS Monaco",
    "лиль": "LOSC Lille", "lille": "LOSC Lille", "losc lille": "LOSC Lille",
    "ренн": "Stade Rennais FC", "rennes": "Stade Rennais FC", "stade rennais": "Stade Rennais FC", "ренн": "Stade Rennais FC",
    "ницца": "OGC Nice", "nice": "OGC Nice", "ogc nice": "OGC Nice",
    "страсбур": "RC Strasbourg", "strasbourg": "RC Strasbourg", "rc strasbourg": "RC Strasbourg",
    "брест": "Stade Brestois 29", "brest": "Stade Brestois 29",
    "тулуза": "Toulouse FC", "toulouse": "Toulouse FC",
    # Другие клубы
    "бенфика": "Benfica", "benfica": "Benfica", "спортинг лиссабон": "Sporting", "sporting": "Sporting", "спортинг": "Sporting", "sporting cp": "Sporting",
    "порту": "FC Porto", "porto": "FC Porto", "fc porto": "FC Porto",
    "аякс": "Ajax", "ajax": "Ajax", "аякс амстердам": "Ajax", "ajax amsterdam": "Ajax",
    "псв": "PSV", "psv": "PSV", "псв эйндховен": "PSV", "psv eindhoven": "PSV", "эйндховен": "PSV", "eindhoven": "PSV",
    "фейеноорд": "Feyenoord", "feyenoord": "Feyenoord",
    "селтик": "Celtic", "celtic": "Celtic",
    "рейнджерс": "Rangers", "rangers": "Rangers",
    "брюгге": "Club Brugge", "club brugge": "Club Brugge", "brugge": "Club Brugge",
    "андерлехт": "Anderlecht", "anderlecht": "Anderlecht",
    "бока хуниорс": "Boca Juniors", "boca juniors": "Boca Juniors", "бока": "Boca Juniors", "boca": "Boca Juniors",
    "ривер плейт": "River Plate", "river plate": "River Plate", "ривер": "River Plate", "river": "River Plate",
    "индепендьенте": "Independiente", "independiente": "Independiente",
    "расинг": "Racing Club", "racing club": "Racing Club", "racing": "Racing Club",
    "сан лоренсо": "San Lorenzo", "san lorenzo": "San Lorenzo",
    "аталанта юнайтед": "Atlanta United", "atlanta united": "Atlanta United", "atlanta": "Atlanta United",
    "ла галакси": "LA Galaxy", "la galaxy": "LA Galaxy", "galaxy": "LA Galaxy",
    "интер майами": "Inter Miami CF", "inter miami": "Inter Miami CF", "inter miami cf": "Inter Miami CF", "miami": "Inter Miami CF",
    "сиэтл": "Seattle Sounders FC", "seattle sounders": "Seattle Sounders FC", "seattle": "Seattle Sounders FC",
    "торонто": "Toronto FC", "toronto fc": "Toronto FC", "toronto": "Toronto FC",
    "монреаль": "CF Montréal", "cf montreal": "CF Montréal", "montreal": "CF Montréal",
    "крус асуль": "Cruz Azul", "cruz azul": "Cruz Azul",
    "америка": "America", "america": "America", "club america": "America",
    "гуадалахара": "Guadalajara", "guadalajara": "Guadalajara", "чикаритос": "Guadalajara",
    "монтеррей": "Monterrey", "monterrey": "Monterrey",
    "аль хиляль": "Al Hilal", "al hilal": "Al Hilal", "хиляль": "Al Hilal", "hilal": "Al Hilal",
    "аль насср": "Al Nassr", "al nassr": "Al Nassr", "насср": "Al Nassr", "nassr": "Al Nassr",
    "аль иттихад": "Al Ittihad", "al ittihad": "Al Ittihad", "иттихад": "Al Ittihad", "ittihad": "Al Ittihad",
    "зенит": "Zenit", "zenit": "Zenit", "зенит спб": "Zenit",
    "шахтёр": "Shakhtar Donetsk", "shakhtar": "Shakhtar Donetsk", "шахтер": "Shakhtar Donetsk", "donetsk": "Shakhtar Donetsk",
    # Сборные (рус / англ)
    "аргентина": "Argentina", "argentina": "Argentina",
    "бразилия": "Brazil", "brazil": "Brazil",
    "германия": "Germany", "germany": "Germany", "немцы": "Germany",
    "франция": "France", "france": "France",
    "испания": "Spain", "spain": "Spain",
    "италия": "Italy", "italy": "Italy",
    "англия": "England", "england": "England",
    "португалия": "Portugal", "portugal": "Portugal",
    "голландия": "Netherlands", "netherlands": "Netherlands", "нидерланды": "Netherlands", "holland": "Netherlands",
    "бельгия": "Belgium", "belgium": "Belgium",
    "польша": "Poland", "poland": "Poland",
    "украина": "Ukraine", "ukraine": "Ukraine",
    "хорватия": "Croatia", "croatia": "Croatia",
    "швейцария": "Switzerland", "switzerland": "Switzerland",
    "сша": "United States", "united states": "United States", "америка сша": "United States", "usa": "United States",
    "мексика": "Mexico", "mexico": "Mexico",
    "канада": "Canada", "canada": "Canada",
    "шотландия": "Scotland", "scotland": "Scotland",
    "уэльс": "Wales", "wales": "Wales",
    "чехия": "Czechia", "czechia": "Czechia",
    "румыния": "Romania", "romania": "Romania",
    "швеция": "Sweden", "sweden": "Sweden",
    "дания": "Denmark", "denmark": "Denmark",
    "норвегия": "Norway", "norway": "Norway",
    "финляндия": "Finland", "finland": "Finland",
    "ирландия": "Republic of Ireland", "republic of ireland": "Republic of Ireland", "ireland": "Republic of Ireland",
    "северная ирландия": "Northern Ireland", "northern ireland": "Northern Ireland",
    "китай": "China", "china": "China",
    "катар": "Qatar", "qatar": "Qatar",
    "марокко": "Morocco", "morocco": "Morocco",
    "гана": "Ghana", "ghana": "Ghana",
    "венгрия": "Hungary", "hungary": "Hungary",
    "исландия": "Iceland", "iceland": "Iceland",
}


def get_team_suggestions(query: str, limit: int = 10) -> list[dict]:
    """
    Подсказки для поля «Команда»: по запросу (кириллица, латиница, любой язык) возвращает
    список команд с каноническим названием и логотипом для подстановки.
    """
    q = _normalize(query)
    if not q or len(q) < 2:
        return []
    seen = set()
    result = []
    # 1) Прямое совпадение по алиасу: "барселона" -> FC Barcelona
    canonical = TEAM_ALIASES.get(q)
    if canonical:
        if canonical not in seen:
            seen.add(canonical)
            result.append({"team_name": canonical, "logo_url": get_logo_url(canonical)})
    # 2) Все канонические имена (клубы + сборные)
    all_teams = list(CLUBS) + list(WOMEN_CLUBS) + list(dict.fromkeys(NATIONAL_TEAMS_MEN + NATIONAL_TEAMS_WOMEN))
    for team in all_teams:
        if len(result) >= limit:
            break
        if team in seen:
            continue
        t_lower = _normalize(team)
        if q in t_lower or t_lower in q:
            seen.add(team)
            result.append({"team_name": team, "logo_url": get_logo_url(team)})
    # 3) По алиасам: если запрос входит в алиас
    for alias, canonical in TEAM_ALIASES.items():
        if len(result) >= limit:
            break
        if canonical in seen:
            continue
        if q in alias or alias in q:
            seen.add(canonical)
            result.append({"team_name": canonical, "logo_url": get_logo_url(canonical)})
    return result[:limit]
