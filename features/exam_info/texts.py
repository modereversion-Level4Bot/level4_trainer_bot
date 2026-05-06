"""Texts for exam info feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def exam_info_overview_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "ℹ️ <b>Как проходит экзамен</b>\n\n"
            "Предлагаем Вам обратить внимание на порядок прохождения экзамена.\n\n"
            "Тестирующая система состоит из трёх частей:\n\n"
            "🎙 <b>Интервью</b>\n"
            "🛫 <b>Ролевая игра</b> — маршрут\n"
            "🧾 <b>Послеполетный разбор</b> - новости и вопросы\n\n"
            "⏱ Общая продолжительность экзамена: примерно <b>25–40 минут</b>."
        )
    return (
        "ℹ️ <b>How the exam works</b>\n\n"
        "Please pay attention to the structure of the exam.\n\n"
        "The test consists of three parts:\n\n"
        "🎙 <b>Interview</b>\n"
        "🛫 <b>Role play</b> — route\n"
        "🧾 <b>Post-flight debrief</b> - news and route questions\n\n"
        "⏱ Total exam duration: about <b>25–40 minutes</b>."
    )


def exam_info_interview_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🎙 <b>Интервью</b>\n\n"
            "Интервью — вводная часть тестирования. Обычно оно длится <b>5–6 минут</b>.\n\n"
            "Экзаменатор представляет себя, объясняет порядок проведения теста и задаёт один из "
            "разминочных вопросов:\n\n"
            "• <i>Could you tell me a little about yourself?</i>\n"
            "• <i>What is your background in aviation?</i>\n\n"
            "Эти вопросы помогают настроиться на работу и начать говорить.\n\n"
            "Далее начинается основное интервью. В нём задаются вопросы, связанные с "
            "профессиональной деятельностью пилота.\n\n"
            "📌 Такие вопросы можно тренировать в разделе <b>🎙 Вопросы</b>."
        )
    return (
        "🎙 <b>Interview</b>\n\n"
        "The interview is the introductory part of the test. It usually lasts <b>5–6 minutes</b>.\n\n"
        "The examiner introduces themselves, explains the test procedure, and asks one of the "
        "warm-up questions:\n\n"
        "• <i>Could you tell me a little about yourself?</i>\n"
        "• <i>What is your background in aviation?</i>\n\n"
        "These questions help you get into speaking mode.\n\n"
        "After that, the main interview begins. The questions are related to the pilot’s "
        "professional activity.\n\n"
        "📌 You can practise these questions in the <b>🎙 Questions</b> section."
    )


def exam_info_role_play_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🛫 <b>Ролевая игра</b>\n\n"
            "Вторая часть тестирования длится примерно <b>15–17 минут</b>.\n\n"
            "Она включает:\n\n"
            "🧭 предполетный брифинг\n"
            "📻 розыгрыш этапа полёта\n"
            "🎧 реальные отрывки радиообмена\n"
            "🧑‍✈️ ответы пилота по стандартной фразеологии\n\n"
            "Во время брифинга экзаменатор знакомит Вас с метеорологической и навигационной "
            "обстановкой, а также с особенностями аэропорта.\n\n"
            "В процессе ролевой игры экзаменатор включает фрагменты радиообмена. Экзаменуемый "
            "должен давать чёткие ответы в соответствии со стандартной фразеологией.\n\n"
            "Каждый маршрут содержит внештатную ситуацию:\n\n"
            "• отказ двигателя\n"
            "• выкатывание\n"
            "• пожар\n"
            "• больной пассажир\n"
            "• другие нестандартные события\n\n"
            "📌 Маршруты, аудио, расшифровки и варианты ответов можно тренировать в разделе\n "
            "<b>🛫 Маршруты</b>."
        )
    return (
        "🛫 <b>Role play</b>\n\n"
        "The second part of the test lasts about <b>15–17 minutes</b>.\n\n"
        "It includes:\n\n"
        "🧭 pre-flight briefing\n"
        "📻 flight-stage role play\n"
        "🎧 real ATC communication excerpts\n"
        "🧑‍✈️ pilot responses using standard phraseology\n\n"
        "During the briefing, the examiner explains the weather and navigation situation, as well as "
        "airport-specific details.\n\n"
        "During the role play, the examiner plays ATC communication fragments. The examinee must give "
        "clear responses according to standard phraseology.\n\n"
        "Each route includes an abnormal situation:\n\n"
        "• engine failure\n"
        "• runway excursion\n"
        "• fire\n"
        "• sick passenger\n"
        "• other non-standard events\n\n"
        "📌 Routes, audio tracks, transcripts, and sample responses can be practised in the "
        "<b>🛫 Routes</b>\n "
        "section."
    )


def exam_info_post_flight_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🧾 <b>Послеполетный разбор</b>\n\n"
            "Третья и заключительная часть занимает примерно <b>5–6 минут</b>.\n\n"
            "Сначала экзаменатор задаёт вопросы по маршруту из второй части и играет роль инспектора "
            "SAFA.\n\n"
            "Экзаменуемый в этот момент — член экипажа, который только что выполнил полёт.\n\n"
            "После вопросов следуют <b>Новости</b>.\n\n"
            "Экзаменуемому предлагается прослушать радионовость длительностью около <b>40 секунд</b> "
            "о выполненном рейсе и высказать мнение о достоверности услышанной информации.\n\n"
            "📌 Новости и вопросы по маршруту можно тренировать в конце прохождения конкретного "
            "маршрута.\n\n"
            "✅ На этом экзамен заканчивается."
        )
    return (
        "🧾 <b>Post-flight debrief</b>\n\n"
        "The third and final part takes about <b>5–6 minutes</b>.\n\n"
        "First, the examiner asks questions about the route from the second part and acts as a SAFA "
        "inspector.\n\n"
        "At this stage, the examinee is a crew member who has just completed the flight.\n\n"
        "After the questions, there is a <b>News</b> task.\n\n"
        "The examinee listens to a radio news item of about <b>40 seconds</b> about the completed "
        "flight and gives an opinion on whether the information is accurate.\n\n"
        "📌 News and route questions can be practised at the end of a specific route.\n\n"
        "✅ This completes the exam."
    )


def interview_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🎙 Как проходит интервью?"
    return "🎙 Interview"


def role_play_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🛫 Ролевая игра"
    return "🛫 Role play"


def post_flight_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🧾 Послеполетный разбор"
    return "🧾 Post-flight debrief"


def back_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ Назад"
    return "⬅️ Back"


def main_menu_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🏠 Главное меню"
    return "🏠 Main menu"
