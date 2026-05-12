# Подготовка деплоя в Railway

## Цель

Развернуть `Level4Trainer` как один Python-сервис в режиме polling.

## Start command

В Railway должен использоваться:

```bash
python run.py
```

## Разделение токенов (dev vs official)

Обязательное правило для polling-режима:
- `dev/test BOT_TOKEN` используется только локально;
- `official BOT_TOKEN` используется только в Railway (production/staging);
- один и тот же `BOT_TOKEN` нельзя запускать одновременно в двух polling-процессах;
- если Railway уже запущен с official token, локально этот же official token запускать нельзя.

## Переменные окружения в Railway

Рекомендуемый минимальный набор:
- `BOT_TOKEN`
- `ADMIN_IDS`
- `APP_ENV=production`
- `DB_PATH`
- `BOT_VERSION`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
- `MEDIA_PRELOAD_CHAT_ID`
- `MEDIA_PRELOAD_DELAY_SECONDS`

## SQLite / `DB_PATH` в Railway

`DB_PATH` определяет путь к файлу SQLite.
SQLite допустим для MVP, но для Railway важно подключить persistent volume.

Ключевые правила:
- без persistent volume: данные не гарантированно сохраняются;
- с persistent volume: база сохраняется между перезапусками.
- для production/MVP deploy `DB_PATH` должен указывать путь внутри volume;
- файл БД не должен попадать в GitHub.

Пример:
- `DB_PATH=/data/level4_trainer.db` (где `/data` смонтирован как Railway Volume).

Каноническая политика путей:
- local/dev: `data/local/dev_main.db`;
- Railway production: `/data/level4_trainer.db`.

## Media / audio стратегия

Для `🎙 Questions`:
- `media/questions/*.mp3` не хранятся в GitHub;
- локальные mp3 нужны только для `python scripts/preload_question_audio.py`;
- runtime отправляет пользователю audio по Telegram `file_id` из `media_assets` (не из локального файла);
- если production DB новая и `media_assets` пустая, нужно выполнить:
  1) `python scripts/import_questions.py`  
  2) `python scripts/preload_question_audio.py`.

Исходные audio-файлы нужно хранить отдельно от GitHub:
- локальный защищенный backup;
- cloud storage;
- Railway volume;
- или другой согласованный storage.

Для `🛣 Routes`:
- source media paths в Sheets указываются относительно `media/routes/`
  (например, `route_001/images/pic.jpeg`, `route_001/audio/file.mp3`);
- preload images: `python scripts/preload_route_images.py`;
- preload audio: `python scripts/preload_route_audio.py`;
- или unified pipeline: `python scripts/preload_route_media.py --types audio,image`;
- runtime для route images использует `media_assets` (`file_id`) с fallback на local file;
- runtime для route audio использует только `media_assets` (`file_id`) без local upload в user chat.

## Official Questions audio cache ops (MVP)

Source of truth для official Questions audio cache:
- таблица `media_assets`;
- `feature='questions'`;
- `content_type='question_audio'`.

Official preload/cutover считается закрытым только если:
- `question_audio` со `status='ready'` = `261`;
- `question_audio` с non-empty `file_id` = `261`;
- audio smoke в official bot пройден.

Операционные скрипты (MVP):
- `python scripts/preload_question_audio.py`
- `python scripts/export_question_audio_media_assets.py`
- `python scripts/import_question_audio_media_assets_from_env.py`
- `python scripts/diagnose_railway_db.py`

Если payload не помещается в одну Railway variable, используйте chunked gzip переменные:
- `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNKS`
- `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNK_001`
- `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNK_002`

Важно:
- после любых temporary Railway Start Command для диагностики/импорта вернуть Start Command на `python run.py`;
- текущий workflow — MVP-операционный; далее планируется более безопасный контур через Admin Content Import / Google Drive audio workflow.

## Рекомендуемый порядок перед production запуском

1. Подготовить env vars в Railway.
2. Проверить, что `DB_PATH` указывает на Railway Volume.
3. Выполнить импорт контента (`grammar`, `questions`) и preload audio.
4. Запустить сервис командой `python run.py`.
5. Проверить `/start` и базовый smoke в Telegram.
