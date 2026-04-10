# Отчёт по проекту FC26 Django

**Дата:** 14 марта 2025 (обновлено)  
**Проект:** fc26-django (турниры в стиле FC 26, аккаунты, подписки, платежи)

---

## 1. Структура проекта

| Компонент | Путь | Назначение |
|-----------|------|------------|
| Конфиг проекта | `fc26_django/` | settings, urls, wsgi, asgi, middleware |
| Приложение аккаунтов | `accounts/` | Регистрация, профили, подписки, платежи |
| Приложение турниров | `tournament/` | Турниры FC 26, группы, плей-офф, команды |
| Шаблоны | `templates/` | Все HTML-шаблоны проекта |
| Зависимости | `requirements.txt` | Список пакетов |
| Окружение | `.env`, `.env.example` | Секреты и пример конфигурации |

---

## 2. Установленные приложения (settings.py)

- **Django:** admin, auth, contenttypes, sessions, messages, staticfiles, sites, **sitemaps**
- **accounts** — своё приложение
- **tournament** — своё приложение
- **django-allauth:** allauth, allauth.account, allauth.socialaccount, allauth.socialaccount.providers.google

**Доп. настройки:**
- `SITE_ID = 1`
- Бэкенды аутентификации: ModelBackend + AuthenticationBackend (allauth)
- `LOGIN_REDIRECT_URL = '/'`, `LOGOUT_REDIRECT_URL = '/'`, `LOGIN_URL = '/accounts/login/'`
- Allauth: email обязателен, верификация `mandatory`, адаптер `accounts.adapters.AccountAdapter`
- Google OAuth: scope profile + email
- Email: из .env (SMTP) или консольный бэкенд
- БД: SQLite по умолчанию; при наличии `DATABASE_URL` — PostgreSQL через dj-database-url
- Языки: ru (по умолчанию), en, de, es, fr, pt, uk, kk
- `LOCALE_PATHS = [BASE_DIR / 'locale']`
- Статика: `STATIC_URL = 'static/'`, `STATIC_ROOT = staticfiles`, `MEDIA_URL = 'media/'`, `MEDIA_ROOT = media`
- Платежи: 2Checkout и Robokassa (ключи из .env)
- Production: при `DEBUG=False` или `DJANGO_ENV=production` — CSRF_TRUSTED_ORIGINS, SECURE_SSL_REDIRECT, secure cookies, HSTS (опционально)

---

## 3. Middleware

1. SecurityMiddleware  
2. SessionMiddleware  
3. LocaleMiddleware  
4. CommonMiddleware  
5. **LocaleFromIPMiddleware** (fc26_django) — определение языка по IP (ip-api.com)  
6. CsrfViewMiddleware  
7. AuthenticationMiddleware  
8. AccountMiddleware (allauth)  
9. MessageMiddleware  
10. XFrameOptionsMiddleware  

---

## 4. Маршруты (URLs)

### Корневой `fc26_django/urls.py`
- `/admin/` — админка Django  
- `/i18n/setlang/` — смена языка  
- `/accounts/` — подключает `accounts.urls`  
- `/` — подключает `tournament.urls`  

### accounts/urls.py
| URL | Назначение |
|-----|------------|
| `profile/` | Профиль пользователя |
| `profiles/` | Список игровых профилей |
| `profiles/create/` | Создание игрового профиля |
| `profiles/<id>/stats/` | Статистика игрового профиля |
| `subscription/` | Страница подписки |
| `subscription/checkout/` | Оформление подписки |
| `subscription/success/` | Успешная оплата подписки |
| `payment/robokassa/result/` | Callback Robokassa |
| `payment/robokassa/success/` | Успех оплаты Robokassa |
| `payment/robokassa/fail/` | Ошибка оплаты Robokassa |
| `register/` | Редирект на signup allauth |
| `''` | Allauth URLs (login, signup, logout, password reset и т.д.) |

### tournament/urls.py
| URL | Назначение |
|-----|------------|
| `''` | Главная (index) |
| `setup/` | Настройка турнира |
| `tournament/` | Страница турнира |
| `tournament/playoff/` | Плей-офф |
| `tournament/history/` | История турниров |
| `tournament/<id>/` | Выбор турнира |
| `update_match/<id>/` | Обновление матча |
| `api/generate-teams/` | API: генерация команд |
| `api/team-suggestions/` | API: подсказки команд |
| `api/group-stage-status/` | API: статус группового этапа |
| `create_playoff/` | Создание плей-офф |
| `reset/` | Сброс турнира |
| `highlight/match/<id>/` | Создание хайлайта матча |
| `highlight/tournament/` | Создание хайлайта турнира |
| `m/<slug>/` | Публичная ссылка на матч |
| `t/<slug>/` | Публичная ссылка на турнир |

---

## 5. Модели и миграции

### accounts
| Модель | Описание |
|--------|----------|
| **GameProfile** | user, nickname, avatar, is_primary |
| **ProfileStats** | 1:1 к GameProfile — матчи, голы, винрейт |
| **UserProfile** | 1:1 к User — plan (free/monthly/yearly), subscription_type, subscription_ends_at |
| **PendingSubscriptionPayment** | user, plan, provider (2checkout/robokassa), amount |

**Миграции:** 0001_initial, 0002_userprofile_subscription_type, 0003_game_profiles_and_stats, 0004_pending_subscription_payment  

### tournament
| Модель | Описание |
|--------|----------|
| **Team** | name, rating, star_rating, tier (команды FC 26) |
| **Settings** | название, описание, тип (round_robin/bracket), is_double_round, has_group_stage, owner |
| **TournamentTeamSettings** | настройки генерации команд PRO (min/max rating, tiers, unique_teams и т.д.) |
| **AssignedTeam** | турнир, команда, round_num (PRO) |
| **Group** | settings, name, order (групповой этап) |
| **Player** | settings, game_profile (опционально), name, team_name, color, seed, logo_url, group |
| **Match** | settings, round_num, home/away, next_match, winner_slot, group, scores, is_played, station, notes |
| **MatchHighlight** | match, slug, created_by — публичная ссылка на матч |
| **TournamentHighlight** | tournament, slug, created_by — публичная ссылка на турнир |

**Миграции:** 0001–0016 (включая bracket, groups, teams, star_ratings, highlights, populate_teams, populate_star_ratings и др.)  

---

## 6. Шаблоны (27 файлов)

### Базовые и главные
- `base.html` — базовый шаблон  
- `index.html` — главная  
- `tournament.html` — турнир  
- `playoff.html` — плей-офф  

### accounts
- `accounts/register.html`, `accounts/login.html`, `accounts/profile.html`  
- `accounts/subscription.html`, `accounts/payment_redirect.html`  
- `accounts/game_profiles_list.html`, `accounts/game_profile_create.html`, `accounts/game_profile_stats.html`  

### account (allauth)
- `account/login.html`, `signup.html`, `logout.html`  
- `account/email_confirm.html`, `verification_sent.html`, `verified_email_required.html`  
- `account/password_reset.html`, `password_reset_done.html`, `password_reset_from_key.html`, `password_reset_from_key_done.html`  

### socialaccount
- `socialaccount/login.html`  

### tournament
- `tournament/history.html`  
- `tournament/match_highlight.html`, `tournament/tournament_highlight.html`, `tournament/highlight_404.html`  

---

## 7. Файлы приложений

### accounts
- `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`  
- `signals.py`, `adapters.py`, `context_processors.py`, `services.py`, `payments.py`, `tests.py`, `apps.py`  

### tournament
- `models.py`, `views.py`, `urls.py`, `admin.py`, `ea_fc26_teams.py`, `tests.py`, `apps.py`  
- **services:** `profile_stats.py`, `team_generator.py`, `star_ratings_fetcher.py`  
- **management/commands:** `update_star_ratings.py`  

---

## 8. Зависимости (requirements.txt)

- Django>=6.0  
- django-allauth>=65.0  
- PyJWT>=2.0  
- requests>=2.28  
- python-dotenv>=1.0  
- Pillow>=10.0  
- gunicorn>=21.0  
- dj-database-url>=2.0  

---

## 9. Окружение (.env.example)

**Django:** SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS; для production — CSRF_TRUSTED_ORIGINS, DATABASE_URL, SECURE_SSL_REDIRECT, SECURE_HSTS_*  

**Email (Gmail):** EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL  

**2Checkout:** TWOCHECKOUT_SID, TWOCHECKOUT_SECRET_WORD, TWOCHECKOUT_DEMO  

**Robokassa:** ROBOKASSA_LOGIN, ROBOKASSA_PASSWORD1, ROBOKASSA_PASSWORD2, ROBOKASSA_TEST  

---

## 10. Что готово (полный чеклист)

### Конфиг и инфраструктура
- [x] **fc26_django/settings.py** — все настройки: INSTALLED_APPS, middleware, БД, i18n, static/media, email, 2Checkout, Robokassa, production security
- [x] **fc26_django/urls.py** — корневые маршруты: admin, i18n/setlang, accounts, tournament
- [x] **fc26_django/wsgi.py**, **asgi.py** — точки входа
- [x] **fc26_django/middleware.py** — LocaleFromIPMiddleware (язык по IP)
- [x] **requirements.txt** — Django 6+, allauth, PyJWT, requests, python-dotenv, Pillow, gunicorn, dj-database-url
- [x] **.env.example** — шаблон переменных (Django, Email, 2Checkout, Robokassa)
- [x] Загрузка .env через python-dotenv в settings

### Установленные приложения
- [x] django.contrib: admin, auth, contenttypes, sessions, messages, staticfiles, sites, sitemaps
- [x] **accounts** — своё приложение
- [x] **tournament** — своё приложение
- [x] **allauth** + account + socialaccount + providers.google

### Маршруты и представления
- [x] **accounts:** profile, profiles (list/create/stats), subscription (страница, checkout, success), payment/robokassa (result/success/fail), register → allauth, allauth.urls
- [x] **tournament:** index, setup, tournament, playoff, history, tournament/<id>, update_match, api/generate-teams, api/team-suggestions, api/group-stage-status, create_playoff, reset, highlight (match/tournament), m/<slug>, t/<slug>

### Модели и миграции
- [x] **accounts:** GameProfile, ProfileStats, UserProfile, PendingSubscriptionPayment — миграции 0001–0004
- [x] **tournament:** Team, Settings, TournamentTeamSettings, AssignedTeam, Group, Player, Match, MatchHighlight, TournamentHighlight — миграции 0001–0016

### Шаблоны (27 файлов)
- [x] base.html, index.html, tournament.html, playoff.html
- [x] accounts: register, login, profile, subscription, payment_redirect, game_profiles_list, game_profile_create, game_profile_stats
- [x] account (allauth): login, signup, logout, email_confirm, verification_sent, verified_email_required, password_reset (4 шаблона)
- [x] socialaccount/login.html
- [x] tournament: history, match_highlight, tournament_highlight, highlight_404

### Файлы приложений
- [x] **accounts:** models, views, urls, forms, admin, signals, adapters, context_processors, services, payments, tests, apps
- [x] **tournament:** models, views, urls, admin, ea_fc26_teams, tests, apps; services (profile_stats, team_generator, star_ratings_fetcher); management command update_star_ratings

### Что не готово / ограничено
- [ ] **Статика:** своей папки `static/` в репозитории нет — только STATIC_URL и {% load static %} в шаблонах
- [ ] **Тесты:** в accounts/tests.py и tournament/tests.py только заглушки
- [ ] **Фикстуры:** нет
- [ ] **README:** нет; документация — комментарии в коде, .env.example и этот PROJECT_REPORT.md

---

## 11. Функционально реализовано

- **Авторизация:** регистрация, вход, выход, сброс пароля, обязательная верификация email, вход через Google.  
- **Профили:** пользовательский профиль, игровые профили (ник, аватар, статистика).  
- **Подписки и платежи:** страница подписки, оформление (checkout), 2Checkout и Robokassa (в т.ч. callback Robokassa, success/fail).  
- **Турниры FC 26:** настройка (round-robin/bracket, групповой этап), команды из базы (рейтинг, звёзды, тиры), генерация команд и подсказки по API, обновление матчей, создание плей-офф, сброс турнира.  
- **Публичные ссылки:** хайлайты матча (`m/<slug>/`) и турнира (`t/<slug>/`).  
- **Локализация:** определение языка по IP (middleware), смена языка, 8 языков, sitemaps в INSTALLED_APPS.  
- **Деплой:** gunicorn, dj-database-url, настройки безопасности для production.  

---

## 12. Рекомендации на будущее

1. Добавить реальные тесты в `accounts/tests.py` и `tournament/tests.py`.  
2. При необходимости — фикстуры для команд/настроек.  
3. Добавить README.md (установка, .env, запуск, деплой).  
4. При необходимости — свои статические файлы (CSS/JS) в `static/` и вызов `collectstatic` перед деплоем.  

---

*Отчёт сформирован автоматически по состоянию репозитория.*
