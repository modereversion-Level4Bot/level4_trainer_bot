# Локальный запуск Level4Trainer

Ниже — базовая последовательность запуска проекта на локальной машине.

## 1) Создать `venv`

```bash
python -m venv .venv
```

## 2) Активировать `venv`

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

## 3) Установить зависимости

```bash
pip install -r requirements.txt
```

## 4) Скопировать `.env.example` в `.env`

```bash
copy .env.example .env
```

## 5) Заполнить `BOT_TOKEN`

Откройте файл `.env` и укажите:
- `BOT_TOKEN=<токен вашего Telegram-бота>`
- `MEDIA_PRELOAD_CHAT_ID=<chat_id служебного чата/админа для preload audio>`
- `DB_PATH=data/local/dev_main.db` (основная локальная рабочая БД)

Остальные переменные можно оставить базовыми на первом запуске.

## 6) Инициализировать SQLite

```bash
python scripts/init_db.py
```

Ожидаемый результат: применены SQL-схемы `001..017`, создан файл базы данных.
Рекомендуемый локальный путь: `data/local/dev_main.db`.

Опционально (если в Google Sheets уже подготовлены листы grammar):

```bash
python scripts/import_grammar.py
```

`import_grammar.py` работает в режиме active-sync:
- строки grammar из Sheets импортируются/обновляются с `is_active=1`;
- строки, которых больше нет в Sheets, переводятся в `is_active=0`;
- прогресс пользователей не очищается.

Опционально (если в Google Sheets уже подготовлен лист `questions`):

```bash
python scripts/import_questions.py
```

Важно: `import_questions.py` работает в режиме full-refresh.
После успешной валидации листа `questions` скрипт пересобирает `exam_questions`
и очищает `exam_question_progress` + `exam_question_state`.
CLI-скрипт не удаляет сообщения Telegram: временное audio очищается runtime-механизмом
в самом боте при следующей навигации пользователя в `🎙 Questions` или через reset progress.

Production guard:
- при `APP_ENV=production` нужен флаг `--allow-full-refresh`;
- без флага импорт завершится отказом:
  `Refusing to run full-refresh import in production without --allow-full-refresh`.

Полезные команды:

```bash
python scripts/import_questions.py --dry-run
APP_ENV=production python scripts/import_questions.py --allow-full-refresh
```

После импорта вопросов выполните preload Telegram `file_id`:

```bash
python scripts/preload_question_audio.py
```

`preload_question_audio.py`:
- читает активные `questions` с непустым `audio_file`;
- загружает аудио в `MEDIA_PRELOAD_CHAT_ID`;
- сохраняет `file_id` в `media_assets`;
- помечает проблемные файлы как `missing/failed/skipped`;
- помечает устаревшие `questions`-assets как `outdated`.

Опционально для `Routes`:

```bash
python scripts/import_routes.py --confirm-import
python scripts/preload_route_images.py
python scripts/preload_route_audio.py
```

Или unified командой:

```bash
python scripts/preload_route_media.py --types audio,image
```

Для `Routes` media основной формат путей в Sheets: относительно `media/routes/`
(например, `route_001/images/...` и `route_001/audio/...`).

## 7) Выполнить smoke-check

```bash
python scripts/smoke_check.py
```

Ожидаемый результат:
- `OK: DB schema initialized.`
- при заполненном `BOT_TOKEN`: `OK: Application built...`

## 8) Запустить бота

```bash
python run.py
```

## 9) Проверить `/start` и onboarding в Telegram

1. Откройте бота в Telegram.
2. Отправьте команду `/start`.
3. Убедитесь, что запускается onboarding:
   - экран выбора языка `🇷🇺 Русский / 🇬🇧 English`;
   - экран выбора часового пояса;
   - экраны советов дня и напоминаний;
   - финальный экран с кнопкой `🚀 Поехали!` / `🚀 Let’s go!`.
4. После завершения onboarding повторите `/start`:
   - бот должен открывать главное меню сразу, без повторного onboarding.

## Security / release hygiene

Перед публикацией репозитория, архива или деплоем:
- проверьте, что в коммит/zip не попадают `.env`, файлы БД, credentials и backup-артефакты;
- убедитесь, что `BOT_TOKEN` и Google credentials заданы только через защищённые env-переменные;
- убедитесь, что `MEDIA_PRELOAD_CHAT_ID` задан на сервере;
- используйте `docs/release_checklist.md` как финальный pre-release чек-лист.
