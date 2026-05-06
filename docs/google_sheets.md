# Интеграция с Google Sheets

## Роль Google Sheets в проекте

`Google Sheets` является **источником контента** для проекта `Level4Trainer`.
В таблицах хранится обучающий материал, который затем импортируется в локальную базу.

Важно: бот работает с SQLite, а не читает данные напрямую из `Google Sheets` во время диалога с пользователем.

## Рабочая модель данных

Контур работы:
`Google Sheets -> импорт/валидация -> SQLite -> Telegram bot`

Это позволяет:
- ускорить ответы бота;
- снизить зависимость от внешнего API во время пользовательской сессии;
- централизованно контролировать качество контента.

## Скрипты импорта

Импорт выполняется отдельными скриптами:
- `scripts/import_grammar.py`
- `scripts/import_questions.py`
- `scripts/preload_question_audio.py`
- `scripts/import_routes.py`
- `scripts/import_all_content.py`

Текущий статус:

- `scripts/import_grammar.py` реализован для листов `grammar_topics` и `grammar_questions`;
- `scripts/import_questions.py` реализован для листа `questions`;
- `scripts/preload_question_audio.py` реализован для preload аудио вопросов в Telegram (`file_id` cache);
- остальные скрипты остаются каркасом для следующих этапов.

Запуск импорта грамматики:

```bash
python scripts/import_grammar.py
```

Запуск импорта вопросов:

```bash
python scripts/import_questions.py
```

Preload аудио после импорта вопросов:

```bash
python scripts/preload_question_audio.py
```

Что делает импорт:

- валидирует заголовки обоих листов строго по названию и порядку;
- импортирует темы и вопросы в SQLite;
- для `grammar` использует active-sync:
  - строки из Sheets импортируются/обновляются с `is_active=1`;
  - строки, отсутствующие в Sheets, переводятся в `is_active=0` (без физического удаления);
  - неактивный grammar-контент не участвует в UI/counts/training;
- для `questions` использует full-refresh: после успешной валидации очищает `exam_questions`, `exam_question_progress`, `exam_question_state`, затем загружает актуальные строки листа;
- в `APP_ENV=production` full-refresh `questions` требует флаг `--allow-full-refresh`;
- `scripts/import_questions.py` (CLI) не удаляет/не отправляет сообщения Telegram: runtime-cleanup временного audio выполняется в bot flow;
- runtime-аудио в `🎙 Questions` отправляется по Telegram `file_id` из `media_assets` (локальные файлы используются только в `preload_question_audio.py`);
- `media/questions/*.mp3` не должны попадать в GitHub (source audio хранится отдельно от репозитория);
- после обновления листа `questions` нужно запускать `preload_question_audio.py`, чтобы обновить `file_id` cache;
- если в `questions` ошибка валидации или 0 строк данных, очистка не выполняется;
- использует `topic_number` как стабильную связь между `grammar_topics` и `grammar_questions`;
- учитывает `topic_type`: `main` входит в основной прогресс, `extra` в основной прогресс не входит.

## Проверка подключения к Google Sheets

Перед реализацией импорта можно выполнить безопасную проверку доступа к таблице:

```bash
python scripts/check_google_sheets.py
```

Скрипт проверяет:

- наличие `GOOGLE_SHEET_ID` в `.env`;
- наличие `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` в `.env`;
- возможность открыть таблицу по `GOOGLE_SHEET_ID`;
- наличие листов `grammar_topics`, `grammar_questions`, `questions`;
- совпадение заголовков листов с ожидаемой структурой;
- количество непустых строк данных после заголовка.

Важно:

- service account должен быть добавлен в `Поделиться / Share` у нужной Google-таблицы;
- скрипт **не** импортирует данные в SQLite;
- скрипт выводит только результат проверки и не печатает секреты (`GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`, `private_key`, полный JSON credentials).

## Планируемые листы (таблицы контента)

В дальнейшем планируется использовать листы:
- `grammar_topics`
- `grammar_questions`
- `questions`
- `routes`
- `route_briefings`
- `route_steps`
- `route_news`
- `route_questions`
- `daily_tips`
- `training_reminders`

## Структура листов для грамматики

Для MVP по разделу `📘 Грамматика` фиксируется простая структура из двух листов:

- `grammar_topics`
- `grammar_questions`

Ожидаемый объём контента:

- `15` основных тем (`topic_type = main`);
- `6` дополнительных тем (`topic_type = extra`);
- у каждой основной темы до `100` вопросов;
- у каждой дополнительной темы до `50` вопросов.
- в текущей рабочей таблице импортируется `1500` вопросов.

Важно:

- основные темы (`main`) входят в основной прогресс грамматики;
- дополнительные темы (`extra`) в основной прогресс **не входят**.

### Лист `grammar_topics`

Колонки:

- `topic_number`
- `topic_type`
- `topic_title_ru`
- `topic_title_en`
- `simple_explanation_ru`
- `simple_explanation_en`
- `detailed_explanation_ru`
- `detailed_explanation_en`

Назначение колонок:

- `topic_number` — порядковый номер темы (пример: `1`, `2`, `3`, `16`).
- `topic_type` — тип темы:
  - `main` — основная тема (входит в прогресс),
  - `extra` — дополнительная тема (не входит в основной прогресс).
- `topic_title_ru` — название темы в RU-интерфейсе.
- `topic_title_en` — название темы в EN-интерфейсе.
- `simple_explanation_ru` — короткое объяснение темы на русском.
- `simple_explanation_en` — короткое объяснение темы на английском.
- `detailed_explanation_ru` — подробное объяснение на русском.
- `detailed_explanation_en` — подробное объяснение на английском.

Примеры строк:

```text
topic_number=1
topic_type=main
topic_title_ru=Present Simple
topic_title_en=Present Simple
simple_explanation_ru=Используется для регулярных действий и фактов.
simple_explanation_en=Used for habits and general facts.
detailed_explanation_ru=...
detailed_explanation_en=...
```

```text
topic_number=16
topic_type=extra
topic_title_ru=Mixed conditionals
topic_title_en=Mixed conditionals
simple_explanation_ru=Смешанные условные конструкции.
simple_explanation_en=Mixed conditional patterns.
detailed_explanation_ru=
detailed_explanation_en=
```

Правила заполнения:

- `topic_number` обязателен и уникален.
- `topic_type` обязателен, допустимы только `main` или `extra`.
- `topic_title_ru` обязателен.
- `topic_title_en` желателен.
- `simple_explanation_ru` обязателен.
- `simple_explanation_en` желателен.
- `detailed_explanation_ru` и `detailed_explanation_en` могут быть пустыми.
- если подробное объяснение пустое, кнопку `📖 Подробнее / 📖 Details` для этого языка не показывать.

### Лист `grammar_questions`

Колонки:

- `topic_number`
- `question_number`
- `question`
- `answer_1`
- `answer_2`
- `answer_3`
- `correct_answer`
- `wrong_explanation_ru`
- `wrong_explanation_en`

Назначение колонок:

- `topic_number` — номер темы из `grammar_topics.topic_number`.
- `question_number` — стабильный номер (идентификатор) вопроса внутри темы (пример: `1`, `2`, `3`, `100`).
- `question` — текст вопроса (английский, одинаковый для RU/EN интерфейса), без вводных `Выберите... / Choose...`.
- `answer_1`..`answer_3` — 3 варианта ответа (одинаковые для RU/EN интерфейса).
- `correct_answer` — номер правильного ответа (`1`, `2`, `3`).
- `wrong_explanation_ru` / `wrong_explanation_en` — короткое объяснение ошибки для popup.

Пример строки:

```text
topic_number=1
question_number=1
question=She ___ to London every week.
answer_1=go
answer_2=goes
answer_3=going
correct_answer=2
wrong_explanation_ru=В Present Simple для he/she/it используется окончание -s.
wrong_explanation_en=In Present Simple, he/she/it takes the -s ending.
```

Правила заполнения:

- `topic_number` обязателен и должен существовать в `grammar_topics`.
- `question_number` обязателен.
- `question` обязателен.
- `answer_1`, `answer_2`, `answer_3` обязательны.
- `correct_answer` обязателен, только `1`, `2`, `3`.
- `wrong_explanation_ru` обязателен.
- `wrong_explanation_en` желателен.

### Правило fallback для EN explanation

`question` и `answer_1..answer_3` language-neutral и не дублируются по языкам.

Если `wrong_explanation_en` пустой, на этапе показа popup допустим fallback на `wrong_explanation_ru`.

## Структура листа questions

Лист:

- `questions`

Колонки (строго по порядку):

- `level`
- `question_number`
- `question_en`
- `audio_file`
- `question_translation_ru`
- `sample_answer_en`
- `sample_answer_translation_ru`

Назначение колонок:

- `level` — уровень экзаменационного вопроса (`4` или `5`).
- `question_number` — порядковый номер вопроса внутри уровня (`1`, `2`, `3` ...).
- `question_en` — текст вопроса на английском, обязательное поле.
- `audio_file` — путь/имя аудиофайла; может быть пустым.
- `question_translation_ru` — перевод вопроса на русский; может быть пустым.
- `sample_answer_en` — пример ответа на английском; может быть пустым.
- `sample_answer_translation_ru` — перевод примера ответа на русский; может быть пустым.

Важно:

- `question_en` и `sample_answer_en` остаются английским контентом для обоих языков интерфейса.
- RU-переводы используются как вспомогательный контент и могут отсутствовать.
- дубли `(level, question_number)` в одном листе не допускаются.
- лист `questions` является source of truth для таблицы `exam_questions`;
- успешный `python scripts/import_questions.py` выполняет full-refresh и сбрасывает Questions progress/state;
- в `APP_ENV=production` нужен флаг `--allow-full-refresh`, иначе импорт завершится отказом;
- `python scripts/import_questions.py --dry-run` выполняет validation/summary без записи в БД;
- локальные файлы из `audio_file` используются на этапе preload (`python scripts/preload_question_audio.py`) для получения Telegram `file_id`;
- runtime отправляет аудио пользователю по `file_id`; если `file_id` не готов, вопрос показывается только текстом без ошибки пользователю;
- для новой production DB (где `media_assets` пустая) после `import_questions` нужно обязательно выполнить `preload_question_audio`;
- если временное Questions audio осталось в чате после CLI-импорта, оно очищается runtime-механизмом при следующем переходе пользователя в `🎙 Questions`/очистке прогресса;
- пустой лист `questions` не должен очищать БД: импорт завершается ошибкой.

Примеры строк:

```text
4 | 1 | Tell me about your flight experience. | audio/questions/l4_q001.mp3 | Расскажите о вашем лётном опыте. | I started my flight training... | Я начал лётную подготовку...
4 | 2 | What do you usually check before a flight? | | Что вы обычно проверяете перед полётом? | Before a flight, I usually check... | Перед полётом я обычно проверяю...
5 | 1 | How would you handle a communication problem with ATC? | audio/questions/l5_q001.mp3 | Как бы вы действовали при проблеме связи с диспетчером? | I would stay calm, clarify the instruction... | Я бы сохранял спокойствие...
```

## Связь Grammar с UX

- Экран `📘 Грамматика` показывает только темы `topic_type = main`.
- Кнопка `📎 Дополнительные материалы` показывается только если существуют темы `topic_type = extra`.
- Экран `📎 Дополнительные материалы` показывает темы `topic_type = extra`.
- Основной прогресс грамматики считается только по темам `main` (`изучено X из 15`).
- Темы `extra` в основной прогресс не входят.
- Кнопка `📖 Подробнее` показывается только если `detailed_explanation` для текущего языка заполнен.
  Если для текущего языка пусто, допустим fallback на второй язык; если оба пустые — кнопку не показывать.
- Кнопка `🎯 Тренировка` показывается только если у темы есть вопросы в `grammar_questions`.
- Тренировка выбирает до `10` случайных вопросов по теме без повторов внутри одной сессии.
- Повторный запуск тренировки может дать другой набор вопросов.
- На экране вопроса бот сам добавляет строку инструкции:
  - RU: `Выберите правильный ответ:`
  - EN: `Choose the correct answer:`

### Какие поля намеренно не используются в MVP

Чтобы структура оставалась понятной контент-менеджеру, в MVP не используются:

- `difficulty`
- `emoji` (отдельной колонкой)
- `short_description` (отдельной колонкой)
- `question_type`
- `created_at`
- `updated_at`

## Поля обязательности медиа

Для контента с медиа используются поля:
- `audio_required`
- `image_required`
- `voice_required`

Базовое правило для будущей диагностики:
- если `*_required = 1`, а путь к медиа пустой — это проблема контента;
- если `*_required = 0`, а путь пустой — это нормальная ситуация.
