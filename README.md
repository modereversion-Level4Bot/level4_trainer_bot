# Level4Trainer Bot

`Level4Trainer` — это Telegram-бот для подготовки пилотов к ICAO English exam и SELCAL-style training.

На текущем этапе в репозитории реализованы:
- модульная структура;
- базовая инициализация SQLite;
- точка входа и polling-запуск;
- onboarding v1.0 (RU/EN, язык, часовой пояс, советы дня, напоминания);
- главное меню v1.0 (RU/EN, прогресс `x из n`, условные кнопки по контенту, справочный раздел `ℹ️ Как проходит экзамен`, TODO-alert только для неготового `🛫 Routes`);
- Grammar UI + training v1.0 (`📘 Грамматика / 📘 Grammar`: список main-тем, `📎 Дополнительно / 📎 Additional`, экран темы, `📖 Подробнее / 📖 Details`, тренировка по теме до 10 вопросов, экран результата, отметка изученной main-темы, compact navigation в учебных экранах);
- Questions UI v1.0 (`🎙 Вопросы / 🎙 Questions`: выбор уровня 4/5, continue/start over, base question, единая кнопка `📚 Question review` с RU/EN-правилами контента, кнопка `🎧 К вопросу / 🎧 To question`, compact navigation `⬅️/🏠/➡️`, экран завершения уровня, runtime-аудио через Telegram `file_id` cache + cleanup временных audio-сообщений);
- settings v1.0 (RU/EN, группировка `Main/Notifications/Account`, изменение языка/часового пояса/советов/напоминаний/звука, reset progress, restart onboarding, delete account для обычных пользователей, вход в `🛠 Управление` для администраторов);
- подготовка к дальнейшей реализации бизнес-логики.

Актуальные параметры onboarding UX:
- `Quick setup`: `Europe/Moscow UTC+3`, советы `21:00`, напоминания `21:00`, звук включен;
- быстрые времена выбора: `09:00`, `12:00`, `18:00`, `21:00`;
- кнопка завершения onboarding: `🚀 Поехали!` / `🚀 Let’s go!`.

Полная логика обучения, админ-функций и контентных разделов пока **не реализована**.

Технические временные решения MVP и post-MVP задачи:
- [`docs/technical_debt.md`](docs/technical_debt.md)

UX-note:
- учебные разделы (`Grammar`, `Questions`) используют compact navigation;
- `Settings` использует compact нижнюю навигацию в подменю (`⬅️` + `🏠`);
- onboarding пока оставлен более объясняющим (без массового compact-режима).

## Технологическая база

- Python 3.11+
- `python-telegram-bot` v21 (polling)
- SQLite
- `python-dotenv`
- JobQueue / APScheduler-compatible setup

## Установка зависимостей

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте его:
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Создание `.env`

Создайте рабочий файл окружения из шаблона:

```bash
copy .env.example .env
```

Заполните обязательный параметр:
- `BOT_TOKEN`

Базовые дополнительные параметры:
- `ADMIN_IDS`
- `APP_ENV`
- `DB_PATH`
- `BOT_VERSION`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
- `MEDIA_PRELOAD_CHAT_ID`

Security note:
- не коммитьте `.env`, `.db` и credentials-файлы;
- перед релизом используйте чек-лист: [`docs/release_checklist.md`](docs/release_checklist.md).

DB policy:
- локально по умолчанию используется `DB_PATH=data/local/dev_main.db`;
- для Railway production используйте `DB_PATH=/data/level4_trainer.db`.

## Инициализация SQLite

Выполните:

```bash
python scripts/init_db.py
```

Скрипт применит SQL-схемы и создаст файл базы данных SQLite по пути из `DB_PATH`
(по умолчанию локально: `data/local/dev_main.db`).

## Smoke-check

Запустите быструю техническую проверку:

```bash
python scripts/smoke_check.py
```

## Локальный запуск бота

```bash
python run.py
```

После запуска откройте бота в Telegram и отправьте `/start`.

## Workflow обновления Questions audio (file_id cache)

Если обновляете контент `questions`/аудио, используйте последовательность:

1. `python scripts/import_questions.py`
   - для production: `APP_ENV=production python scripts/import_questions.py --allow-full-refresh`
   - безопасная проверка без записи: `python scripts/import_questions.py --dry-run`
2. Убедитесь, что локальные файлы доступны по путям из `audio_file`.
3. `python scripts/preload_question_audio.py`
4. Проверьте summary preload (missing/failed должны быть `0`).
5. Запустите бота (или выключите maintenance mode).

Важно:
- runtime-поток `🎙 Questions` отправляет аудио пользователю только по Telegram `file_id`;
- если `file_id` не готов, вопрос показывается в текстовом режиме без пользовательской ошибки;
- `import_questions.py` работает в режиме full-refresh и очищает `exam_question_progress` + `exam_question_state`;
- в `APP_ENV=production` full-refresh заблокирован без `--allow-full-refresh`;
- `import_questions.py` не удаляет и не отправляет Telegram messages.

## Текущий статус `/start`

Команда `/start` запускает onboarding для нового пользователя.
После завершения onboarding команда `/start` открывает главное меню v1.0 без повторной первичной настройки.
