# Technical debt

## MVP temporary decisions / Post-MVP cleanup

1. Questions audio storage and delivery
   - Runtime для `🎙 Questions` уже переведен на Telegram `file_id` cache (`media_assets` + preload script).
   - Локальные файлы `media/questions/...` используются только как source для `python scripts/preload_question_audio.py`.
   - Post-MVP нужно определить production-source для исходных audio-файлов:
     - Railway volume;
     - cloud storage;
     - repository artifact storage;
     - другой централизованный вариант.

2. `import_questions.py` full-refresh
   - Введен production-guard: при `APP_ENV=production` full-refresh запрещен без `--allow-full-refresh`.
   - Добавлен `--dry-run` для validation/summary без записи в БД.
   - Открытый post-MVP вопрос: перейти с full-refresh на sync-стратегию, которая сохраняет пользовательский progress.

3. `temporary_messages` (универсальная таблица временных сообщений)
   - В MVP подключена только для `Questions` audio (`feature="questions"`, `message_type="audio"`).
   - После MVP расширить и унифицировать для:
     - Routes images/audio/voice;
     - service layers;
     - admin temporary messages.

4. Legacy поле `exam_question_state.last_audio_message_id`
   - Новая runtime-логика временного аудио использует `temporary_messages`.
   - `last_audio_message_id` оставлено в схеме только как legacy и кандидат на отдельную миграцию удаления/переноса.

5. TODO endpoints перед релизом
   - `menu:routes` и другие TODO-точки входа нужно пересмотреть перед production-релизом:
     - подтвердить UX/навигацию;
     - удалить устаревшие заглушки;
     - зафиксировать финальные guard/safety условия.

6. `media_assets` coverage
   - Сейчас `media_assets` используется только для `Questions` audio.
   - После MVP расширить/унифицировать для:
     - `Routes` media;
     - сервисных media-слоёв;
     - admin/media preload workflows.
