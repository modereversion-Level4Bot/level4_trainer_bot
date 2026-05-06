# UI Text Catalog — Level 4 Trainer

Документ для быстрого поиска пользовательских текстов (RU/EN) перед развитием `Questions v1.0`.

Важно:
- это каталог-справочник, а не источник истины;
- источником истины остаётся код (`features/.../texts.py`, `.../keyboards.py`);
- callback data, UX и бизнес-логика здесь **не меняются**.

Источники:
- `features/main_menu/texts.py`
- `features/main_menu/keyboards.py`
- `features/exam_info/texts.py`
- `features/exam_info/keyboards.py`
- `features/onboarding/texts.py`
- `features/onboarding/keyboards.py`
- `features/settings/texts.py`
- `features/settings/keyboards.py`
- `features/grammar/texts.py`
- `features/grammar/keyboards.py`
- `features/clean_chat/handlers.py`
- `core/constants.py`
- `core/guards.py`
- `docs/smoke_checks.md` (как вспомогательная проверка UX-потока)

---

## 1. Общие кнопки

### Главное меню (полная кнопка)

RU:
`🏠 Главное меню`

EN:
`🏠 Main menu`

Где используется:
`features/exam_info/texts.py`, `features/settings/texts.py`, `features/grammar/texts.py`

Комментарий:
Кнопка присутствует в большинстве разделов как универсальный выход в main menu.

### Home (compact navigation)

RU/EN:
`🏠`

Где используется:
`features/questions/texts.py`, `features/grammar/texts.py`, `features/settings/keyboards.py` (нижняя навигация подменю)

Комментарий:
Используется в учебных разделах и в нижней навигации Settings-подменю.

### Назад (полный)

RU:
`⬅️ Назад`

EN:
`⬅️ Back`

Где используется:
`features/exam_info/texts.py`, `features/onboarding/texts.py`, `features/settings/keyboards.py`

Комментарий:
Полный back сохранён в onboarding/exam-info и в текстовых action-кнопках (`⬅️ К ...`).

### Назад (compact navigation)

RU/EN:
`⬅️`

Где используется:
`features/questions/texts.py`, `features/settings/keyboards.py`, `features/grammar/texts.py`

Комментарий:
Используется для компактной нижней навигации.

### Назад (пагинация в Grammar)

RU:
`◀️ Назад`

EN:
`◀️ Back`

Где используется:
`features/grammar/texts.py`

Комментарий:
Используется именно как кнопка пагинации в списках Grammar.

### Отмена (settings)

RU:
`⛔ Отмена`

EN:
`⛔ Cancel`

Где используется:
`features/settings/keyboards.py`

Комментарий:
Используется в custom-time/reset/restart/delete подтверждениях.

### Отмена (onboarding)

RU:
`❌ Отмена`

EN:
`❌ Cancel`

Где используется:
`features/onboarding/texts.py`, `features/onboarding/keyboards.py`

Комментарий:
В onboarding используется другой эмодзи, чем в settings.

### К списку тем

RU:
`📁 Темы`

EN:
`📁 Topics`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Повторить

RU:
`🔂 Повторить`

EN:
`🔂 Repeat`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Следующая тема

RU:
`Следующая ➡️`

EN:
`Next ➡️`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Предыдущая тема

RU/EN:
`⬅️`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Вперёд (пагинация)

RU/EN:
`▶️`

Где используется:
`features/grammar/texts.py`

### Включить

RU:
`✅ Включить`

EN:
`✅ Enable`

Где используется:
`features/onboarding/keyboards.py`, `features/settings/keyboards.py`

### Выключить

RU:
`🚫 Выключить` / `🚫 Выключить звук`

EN:
`🚫 Disable` / `🚫 Disable sound`

Где используется:
`features/settings/keyboards.py`

Комментарий:
В onboarding чаще используется формулировка `🚫 Не включать / 🚫 Do not enable`.

---

## 2. Главное меню

### Заголовок и описание меню

RU (ключевые строки):
`✈️ Level 4 Trainer`
`Тренажёр ICAO English для пилотов.`
`Ваш текущий прогресс:`
`Выберите раздел для тренировки:`

EN (ключевые строки):
`✈️ Level 4 Trainer`
`ICAO English trainer for pilots.`
`Your current progress:`
`Choose a section to train:`

Где используется:
`features/main_menu/texts.py` (`main_menu_text`)

### Кнопка Grammar

RU:
`📘 Грамматика`

EN:
`📘 Grammar`

Где используется:
`features/main_menu/texts.py`, `features/main_menu/keyboards.py`

### Кнопка Questions

RU:
`🎙 Вопросы`

EN:
`🎙 Questions`

Где используется:
`features/main_menu/texts.py`, `features/main_menu/keyboards.py`

Комментарий:
На текущем этапе кнопка `🎙 Questions` находится в одном верхнем ряду с `📘 Grammar`.

### Кнопка Routes

RU:
`🛫 Маршруты`

EN:
`🛫 Routes`

Где используется:
`features/main_menu/handlers.py` (TODO alert endpoint)

Комментарий:
Кнопка `🛫 Routes` временно скрыта на главном экране; endpoint `menu:routes` оставлен как future TODO.

### Кнопка Exam Info

RU:
`ℹ️ Как проходит экзамен`

EN:
`ℹ️ How the exam works`

Где используется:
`features/main_menu/texts.py`, `features/main_menu/keyboards.py`

### Кнопка Settings

RU:
`⚙️ Настройки`

EN:
`⚙️ Settings`

Где используется:
`features/main_menu/texts.py`, `features/main_menu/keyboards.py`

### Линии прогресса (динамические)

RU:
`📘 Грамматика — изучено X из Y`
`🎙 Вопросы — пройдено X из Y`
`🛫 Маршруты — пройдено X из Y`

EN:
`📘 Grammar — studied X of Y`
`🎙 Questions — completed X of Y`
`🛫 Routes — completed X of Y`

Где используется:
`features/main_menu/texts.py` (`main_menu_text`)

### Admin status lines

RU:
`🟢 Работает`
`🎮 v <version>`

EN:
`🟢 Running`
`🎮 v <version>`

Где используется:
`features/main_menu/texts.py` (`main_menu_text`, при `context.is_admin`)

---

## 3. Как проходит экзамен

### Экран overview

RU:
`ℹ️ Как проходит экзамен`

EN:
`ℹ️ How the exam works`

Где используется:
`features/exam_info/texts.py` (`exam_info_overview_text`)

### Кнопка интервью

RU:
`🎙 Как проходит интервью?`

EN:
`🎙 Interview`

Где используется:
`features/exam_info/texts.py`, `features/exam_info/keyboards.py`

### Кнопка role play

RU:
`🛫 Ролевая игра`

EN:
`🛫 Role play`

Где используется:
`features/exam_info/texts.py`, `features/exam_info/keyboards.py`

### Кнопка post-flight debrief

RU:
`🧾 Послеполетный разбор`

EN:
`🧾 Post-flight debrief`

Где используется:
`features/exam_info/texts.py`, `features/exam_info/keyboards.py`

### Поток кнопок (4 экрана)

RU/EN навигация:
- `overview` -> `🎙 ...`
- `interview` -> `🛫 ...` + `⬅️ Back` + `🏠 Main menu`
- `role_play` -> `🧾 ...` + `⬅️ Back` + `🏠 Main menu`
- `post_flight` -> `🏠 Main menu`

Где используется:
`features/exam_info/keyboards.py`

Комментарий:
Основные экранные тексты в `features/exam_info/texts.py` достаточно объёмные; в каталоге сохранены ключевые заголовки и кнопки.

---

## 4. Онбординг

### Выбор языка

RU:
`🇷🇺 Русский`

EN:
`🇬🇧 English`

Где используется:
`features/onboarding/keyboards.py` (`build_language_keyboard`)

### Быстрая настройка

RU:
`⚡ Быстрая настройка`

EN:
`⚡ Quick setup`

Где используется:
`features/onboarding/texts.py`, `features/onboarding/keyboards.py`

### Выбор часового пояса (метод)

RU:
`📍 Автоматически`
`🕒 Выбрать вручную`

EN:
`📍 Automatically`
`🕒 Choose manually`

Где используется:
`features/onboarding/keyboards.py` (`build_timezone_choice_keyboard`)

Комментарий:
В тексте экрана явно указано: геолокация используется только для определения часового пояса.

### Кнопка отправки геолокации

RU:
`📍 Отправить геолокацию`

EN:
`📍 Send location`

Где используется:
`features/onboarding/texts.py`, `features/onboarding/keyboards.py`

### Daily tip — включение

RU:
`✅ Включить`
`🚫 Не включать`

EN:
`✅ Enable`
`🚫 Do not enable`

Где используется:
`features/onboarding/keyboards.py` (`build_daily_tip_choice_keyboard`)

### Reminder — включение

RU:
`✅ Включить`
`🚫 Не включать`

EN:
`✅ Enable`
`🚫 Do not enable`

Где используется:
`features/onboarding/keyboards.py` (`build_reminders_choice_keyboard`)

### Пресеты времени

RU/EN:
`09:00`, `12:00`, `18:00`, `21:00`

Где используется:
`features/onboarding/keyboards.py` (`PRESET_TIME_OPTIONS`)

### Другое время

RU:
`⏱️ Другое время`

EN:
`⏱️ Other time`

Где используется:
`features/onboarding/texts.py`, `features/onboarding/keyboards.py`

### Финальная кнопка

RU:
`🚀 Поехали!`

EN:
`🚀 Let’s go!`

Где используется:
`features/onboarding/texts.py`, `features/onboarding/keyboards.py`

### Ключевые onboarding alerts/toasts

RU/EN:
- `✅ Язык установлен: ... / ✅ Language set: ...`
- `✅ Быстрая настройка применена / ✅ Quick setup applied`
- `✅ Часовой пояс установлен: ... / ✅ Time zone set: ...`
- `⚠️ Не удалось определить часовой пояс... / ⚠️ Could not detect the time zone...`
- `⚠️ Время нужно указать в формате... / ⚠️ Time must be in HH:MM format...`
- `⚠️ Профиль пользователя не найден... / ⚠️ User profile was not found...`

Где используется:
`features/onboarding/texts.py`

Комментарий:
Полные тексты onboarding-экранов объёмные; для релиза желательно отдельный copy-audit (см. раздел 12).

---

## 5. Настройки

### Main Settings (группы)

RU:
`🧭 Основные`
`🔔 Уведомления`
`👤 Аккаунт`
`🛠 Управление`
`🏠 Главное меню`

EN:
`🧭 Main`
`🔔 Notifications`
`👤 Account`
`🛠 Management`
`🏠 Main menu`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

### Подменю: Основные

RU:
`🌐 Язык интерфейса`
`🌍 Часовой пояс`

EN:
`🌐 Interface language`
`🌍 Time zone`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

### Подменю: Уведомления

RU:
`🔊 Звуки уведомлений`
`💡 Совет дня по грамматике`
`⏰ Напоминания о тренировках`

EN:
`🔊 Notification sounds`
`💡 Daily grammar tip`
`⏰ Training reminders`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

### Подменю: Аккаунт

RU:
`♻️ Прогресс`
`🔄 Перезапуск`
`🗑 Удалить аккаунт`

EN:
`♻️ Progress`
`🔄 Restart`
`🗑 Delete account`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

Комментарий:
Кнопка удаления не показывается админу (контролируется в keyboard builder).

### Нижняя навигация Settings-подменю (compact)

RU/EN:
`⬅️`
`🏠`

Где используется:
`features/settings/keyboards.py` (Main/Notifications/Account/Language/Timezone/Daily/Reminders/Sound/Reset)

Комментарий:
Опасные confirmation-кнопки (`reset/restart/delete`) остаются текстовыми, не compact.

### Метод часового пояса

RU:
`📍 Автоматически`
`🕒 Вручную`

EN:
`📍 Automatically`
`🕒 Manually`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

### Daily/Reminders — действие

RU:
`✅ Включить`
`🚫 Выключить`
`🕒 Изменить время`
`⏱️ Другое время`

EN:
`✅ Enable`
`🚫 Disable`
`🕒 Change time`
`⏱️ Other time`

Где используется:
`features/settings/keyboards.py`

### Sound — действие

RU:
`✅ Включить звук`
`🚫 Выключить звук`

EN:
`✅ Enable sound`
`🚫 Disable sound`

Где используется:
`features/settings/keyboards.py`

### Reset progress

RU:
`📘 Грамматика`
`🎙 Вопросы`
`🛫 Маршруты`
`⚠️ Весь прогресс`
`♻️ Да, сбросить`

EN:
`📘 Grammar`
`🎙 Questions`
`🛫 Routes`
`⚠️ All progress`
`♻️ Yes, reset`

Где используется:
`features/settings/texts.py`, `features/settings/keyboards.py`

### Restart onboarding

RU:
`🔄 Перезапустить`

EN:
`🔄 Restart`

Где используется:
`features/settings/keyboards.py`

### Delete account confirmations

RU:
`⚠️ Продолжить удаление`
`🗑 Да, удалить аккаунт`

EN:
`⚠️ Continue deletion`
`🗑 Yes, delete account`

Где используется:
`features/settings/keyboards.py`

### Management TODO

RU:
`Раздел будет реализован в следующих задачах.`

EN:
`This section will be implemented in future tasks.`

Где используется:
`features/settings/texts.py` (`management_todo_alert`)

---

## 6. Грамматика

### Экран списка main topics

RU (ключевые строки):
`📘 Грамматика`
`📈 Прогресс X из Y`
`📄 Страница X из Y` (при пагинации)
`Выберите тему:`

EN:
`📘 Grammar`
`📈 Progress X of Y`
`📄 Page X of Y` (при пагинации)
`Choose a topic:`

Где используется:
`features/grammar/texts.py` (`grammar_list_text`)

### Дополнительные материалы

RU:
`📎 Дополнительно`
`⬅️ К грамматике`

EN:
`📎 Additional`
`⬅️ To Grammar`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Карточка темы

RU:
`📖 Подробнее`
`🎯 Тренировка`
`📁 Темы`
`⬅️`
`➡️`

EN:
`📖 Details`
`🎯 Training`
`📁 Topics`
`⬅️`
`➡️`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Training prompt

RU:
`Выберите правильный ответ:`

EN:
`Choose the correct answer:`

Где используется:
`features/grammar/texts.py` (`training_question_text`)

### Training toast (correct)

RU:
`✅ Правильно!`

EN:
`✅ Correct!`

Где используется:
`features/grammar/texts.py` (`training_correct_popup_text`)

### Training popup (incorrect)

RU:
`❌ Неверно!`
или
`❌ Неверно!\n\n<объяснение>`

EN:
`❌ Incorrect!`
или
`❌ Incorrect!\n\n<explanation>`

Где используется:
`features/grammar/texts.py` (`training_incorrect_popup_text`)

### Result titles

RU:
`🎉 Превосходно!`
`✅ Хороший результат`
`📘 Стоит повторить материал`

EN:
`🎉 Excellent!`
`✅ Good result`
`📘 It is better to review the material`

Где используется:
`features/grammar/texts.py`

### Result buttons

RU:
`🔂 Повторить`
`📕 Изучить`
`📁 Темы`
`Следующая ➡️`

EN:
`🔂 Repeat`
`📕 Review`
`📁 Topics`
`Next ➡️`

Где используется:
`features/grammar/texts.py`, `features/grammar/keyboards.py`

### Study marker в списке тем

Формат:
`<Название темы> ✅`

Примеры:
`Present Simple ✅`
`🔁 Present Simple ✅`

Где используется:
`features/grammar/keyboards.py` (`_apply_studied_marker`)

Комментарий:
Маркер ставится суффиксом, не префиксом.

---

## 7. Раздел Questions v1.0

Статус:
**Реализовано для пользовательского flow `🎙 Вопросы / 🎙 Questions` (уровни 4/5).**

### Экран выбора уровней

RU (ключевые строки):
`🎙 Вопросы`
`Выберите уровень для тренировки устной части экзамена.`
`Вопросы нужно слушать, читать и отвечать на них вслух самостоятельно.`

EN:
`🎙 Questions`
`Choose a level to practise the speaking part of the exam.`
`Listen to the questions, read them, and try to answer aloud by yourself.`

Где используется:
`features/questions/texts.py` (`questions_levels_text`)

### Empty screen

RU:
`Раздел пока готовится.`
`Скоро здесь появятся экзаменационные вопросы для тренировки устной части.`

EN:
`This section is being prepared.`
`Exam questions for speaking practice will appear here soon.`

Где используется:
`features/questions/texts.py` (`questions_empty_text`)

### Continue / Start over

RU:
`🔄 Сначала`
`▶️ Продолжить`
`⬅️`
`🏠`

EN:
`🔄 Start over`
`▶️ Continue`
`⬅️`
`🏠`

Где используется:
`features/questions/texts.py`, `features/questions/keyboards.py`

Комментарий:
Порядок строк: `[Start over] [Continue]`, затем `[⬅️] [🏠]`.

### Re-entry messages (started vs completed)

RU:
- started: `Вы уже начали тренировку этого уровня.`
- completed: `Вы уже завершили этот уровень.`

EN:
- started: `You have already started this level.`
- completed: `You have already completed this level.`
- completed question: `Would you like to take it again?`

Где используется:
`features/questions/texts.py` (`continue_start_over_started_text`, `continue_start_over_completed_text`)

### Completed re-entry buttons

RU:
`⬅️`
`🔄 Заново`
`🏠`

EN:
`⬅️`
`🔄 Take again`
`🏠`

Где используется:
`features/questions/texts.py`, `features/questions/keyboards.py` (`build_completed_reentry_keyboard`)

Комментарий:
Для completed уровня отдельный экран: первая строка `[⬅️] [Take again]`, вторая строка `[🏠]`.

### Base question view

RU:
`🎙 Level {level} — Вопрос {current} из {total}`
`Прослушайте или прочитайте вопрос и попробуйте ответить вслух.`
`Вопрос:`

EN:
`🎙 Level {level} — Question {current} of {total}`
`Listen to or read the question and try to answer aloud.`
`Question:`

Где используется:
`features/questions/texts.py` (`question_base_text`)

### Question review button

RU:
`📚 Разбор вопроса`
`🎧 К вопросу`

EN:
`📚 Question review`
`🎧 To question`

Где используется:
`features/questions/texts.py`, `features/questions/keyboards.py`

Комментарий:
Старые отдельные кнопки `🌐 Перевод вопроса`, `💬 Пример ответа`, `🇷🇺 Перевод ответа` убраны из текущего UX.
Условия показа `📚`:
- RU: кнопка показывается при наличии любого review-блока (`question_translation_ru` или `sample_answer_en` или `sample_answer_translation_ru`).
- EN: кнопка показывается только если есть `sample_answer_en`.

### Navigation buttons

RU:
`⬅️`
`➡️`
`✅ Завершить`
`🏠`

EN:
`⬅️`
`➡️`
`✅ Finish`
`🏠`

Где используется:
`features/questions/texts.py`, `features/questions/keyboards.py`

Комментарий:
Для question views используется единый row-pattern:
- first: `[🏠] [➡️]`
- middle: `[⬅️] [🏠] [➡️]`
- last: строка 1 `[⬅️] [✅ Finish]`, строка 2 `[🏠]`
- single: строка 1 `[✅ Finish]`, строка 2 `[🏠]`

### Expanded behavior note

- UX-модель: `Base question` -> `📚 Question review` -> `🎧 To question`.
- RU review показывает: `Вопрос`, `Перевод вопроса` (если есть), `Пример ответа` (если есть), `Перевод ответа` (если есть).
- EN review показывает только: `Question`, `Sample answer` (если есть).
- EN review не показывает: `Question translation`, `Answer translation`.
- Порядок блоков review фиксированный внутри каждого языка.
- Пустые блоки не отображаются.
- `To question` сбрасывает expanded state к base question.
- `Previous/Next/Finish` всегда открывают target question в base view.

### Completion screens

RU:
`✅ Level 4 завершён`
`✅ Level 5 завершён`
`5️⃣ Level 5`
`🔄 Заново`
`🎙 Уровни`

EN:
`✅ Level 4 completed`
`✅ Level 5 completed`
`5️⃣ Level 5`
`🔄 Take again`
`🎙 Levels`

Где используется:
`features/questions/texts.py`, `features/questions/keyboards.py`

### Stale/update alerts

RU:
`Материал обновился. Этот уровень сейчас недоступен.`
`Материал обновился. Открою список уровней.`

EN:
`The content has been updated. This level is currently unavailable.`
`The content has been updated. I’ll open the level list.`

Где используется:
`features/questions/texts.py`

---

## 8. Будущий раздел Routes

Статус:
**Черновик, будет утверждаться отдельно перед Routes v1.0.**

### Базовые пункты (черновик)

RU:
`🛫 Маршруты`
`▶️ Начать`
`📰 Новости`
`❓ Вопросы`
`💡 Подсказка`
`💬 Ответ`
`📻 Транскрипт`

EN:
`🛫 Routes`
`▶️ Start`
`📰 News`
`❓ Questions`
`💡 Hint`
`💬 Answer`
`📻 Transcript`

Где планируется:
`features/routes/*` (будущий этап)

---

## 9. Служебные сообщения

### Guard chain (system-level)

RU:
`—`

EN:
`Access is restricted. Please contact support.`
`Bot is under maintenance. Please try again later.`
`This section is available for admins only.`

Где используется:
`core/constants.py`, `core/guards.py`

Комментарий:
Сейчас системные guard-сообщения заданы только на английском.

### Settings state not found

RU:
`⚠️ Профиль пользователя не найден. Нажмите /start еще раз.`

EN:
`⚠️ User profile was not found. Please use /start again.`

Где используется:
`features/settings/texts.py`

### Onboarding state not found

RU:
`⚠️ Профиль пользователя не найден. Нажмите /start еще раз.`

EN:
`⚠️ User profile was not found. Please use /start again.`

Где используется:
`features/onboarding/texts.py`

### Clean chat

Пользовательские тексты:
`нет`

Где используется:
`features/clean_chat/handlers.py`

Комментарий:
Модуль удаляет входящие сообщения, собственных UI-текстов не формирует.

---

## 10. Toast / Popup / Alert

### Settings — toasts

RU/EN:
- `✅ Язык установлен: ... / ✅ Language set: ...`
- `✅ Часовой пояс установлен: ... / ✅ Time zone set: ...`
- `✅ Советы дня включены... / ✅ Daily tips enabled...`
- `🚫 Советы дня выключены / 🚫 Daily tips disabled`
- `✅ Напоминания включены... / ✅ Training reminders enabled...`
- `🚫 Напоминания выключены / 🚫 Training reminders disabled`
- `🔔 Звуковые оповещения включены / 🔔 Sound notifications enabled`
- `🔕 Звуковые оповещения выключены / 🔕 Sound notifications disabled`
- `✅ Прогресс сброшен / ✅ Progress reset`

Где используется:
`features/settings/texts.py`

### Settings — alerts/warnings

RU/EN:
- `⚠️ Неизвестный вариант часового пояса. / ⚠️ Unknown time zone option.`
- `⚠️ Недопустимое значение времени. / ⚠️ Unsupported time value.`
- `⚠️ Администраторский аккаунт нельзя удалить... / ⚠️ An administrator account cannot be deleted...`
- `⚠️ Не удалось определить часовой пояс... / ⚠️ Could not detect the time zone...`
- `⚠️ Время нужно указать в формате... / ⚠️ Time must be in HH:MM format...`

Где используется:
`features/settings/texts.py`

### Grammar — toasts/alerts

RU/EN:
- `✅ Правильно! / ✅ Correct!`
- `❌ Неверно!... / ❌ Incorrect!...`
- `Тренировка устарела... / The training session has expired...`
- `Вопрос недоступен. / Question is unavailable.`
- `Для этой темы пока нет вопросов. / There are no questions for this topic yet.`
- `Материал недоступен. / Material is unavailable.`

Где используется:
`features/grammar/texts.py`

### Onboarding — toasts/alerts

RU/EN:
- `✅ Язык установлен... / ✅ Language set...`
- `✅ Быстрая настройка применена / ✅ Quick setup applied`
- `✅ Часовой пояс установлен... / ✅ Time zone set...`
- `✅ Советы дня включены... / ✅ Daily tips enabled...`
- `🚫 Советы дня выключены / 🚫 Daily tips disabled`
- `✅ Напоминания включены... / ✅ Training reminders enabled...`
- `🚫 Напоминания выключены / 🚫 Training reminders disabled`
- `⚠️ Не удалось определить часовой пояс... / ⚠️ Could not detect the time zone...`
- `⚠️ Время нужно указать в формате... / ⚠️ Time must be in HH:MM format...`

Где используется:
`features/onboarding/texts.py`

### Management TODO

RU:
`Раздел будет реализован в следующих задачах.`

EN:
`This section will be implemented in future tasks.`

Где используется:
`features/main_menu/texts.py`, `features/settings/texts.py`

---

## 11. Ошибки и fallback-сообщения

### Unknown/stale callback в Settings

Поведение:
`answerCallbackQuery` без дополнительного текста (без падения).

Где используется:
`features/settings/callback_router.py`

### Unknown/stale callback в Onboarding

Поведение:
`answerCallbackQuery` без дополнительного текста (без падения).

Где используется:
`features/onboarding/service.py` (`process_onboarding_callback`)

### Unknown callback в Grammar

RU:
`Материал недоступен.`

EN:
`Material is unavailable.`

Где используется:
`features/grammar/handlers.py`, `features/grammar/texts.py`

### Missing profile fallback

RU:
`⚠️ Профиль пользователя не найден. Нажмите /start еще раз.`

EN:
`⚠️ User profile was not found. Please use /start again.`

Где используется:
`features/onboarding/texts.py`, `features/settings/texts.py`

---

## 12. Нужно проверить позже

- Системные guard-сообщения из `core/constants.py` сейчас только на английском; решить, нужна ли RU-локализация.
- В проекте есть две визуально разные кнопки отмены:
  - onboarding: `❌ Отмена`
  - settings: `⛔ Отмена`
  Проверить, требуется ли унификация.
- В Grammar есть два визуальных стиля back:
  - `◀️ Назад` (пагинация)
  - `⬅️ ...` (контекстная навигация по темам/экранам)
  Проверить, устраивает ли это как осознанный UX-паттерн.
- Часть текстов формируется динамически (прогресс, время, timezone, итоги тренировки); перед релизом сделать выборочную проверку RU/EN пар на живых данных.
- Onboarding-тексты объёмные и критичны для first-run UX; желательно отдельный copy-audit перед релизом.
- Черновики для `Routes` в этом документе предварительные; финализировать отдельно перед `v1.0`.
- В `docs/smoke_checks.md` большой объём текста; при росте `Questions/Routes` лучше вынести smoke-check по разделам в отдельные документы.

