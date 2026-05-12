PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- routes: add bilingual/content-order fields required for Routes v1.0 Sheets import.
ALTER TABLE routes ADD COLUMN route_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE routes ADD COLUMN title_ru TEXT;
ALTER TABLE routes ADD COLUMN title_en TEXT;
ALTER TABLE routes ADD COLUMN briefing_ru TEXT;
ALTER TABLE routes ADD COLUMN briefing_en TEXT;
ALTER TABLE routes ADD COLUMN image_file TEXT;

CREATE INDEX IF NOT EXISTS idx_routes_active_order
    ON routes(is_active, route_order);

-- route_steps: add normalized fields used by constructor import.
ALTER TABLE route_steps ADD COLUMN step_number INTEGER;
ALTER TABLE route_steps ADD COLUMN step_type TEXT;
ALTER TABLE route_steps ADD COLUMN text_ru TEXT;
ALTER TABLE route_steps ADD COLUMN text_en TEXT;
ALTER TABLE route_steps ADD COLUMN image_file TEXT;
ALTER TABLE route_steps ADD COLUMN audio_file TEXT;
ALTER TABLE route_steps ADD COLUMN transcript_ru TEXT;
ALTER TABLE route_steps ADD COLUMN transcript_en TEXT;
ALTER TABLE route_steps ADD COLUMN pilot_answer_ru TEXT;
ALTER TABLE route_steps ADD COLUMN pilot_answer_en TEXT;
ALTER TABLE route_steps ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;

UPDATE route_steps
SET step_number = step_no
WHERE step_number IS NULL;

UPDATE route_steps
SET text_ru = text
WHERE COALESCE(TRIM(text_ru), '') = '';

UPDATE route_steps
SET image_file = image_path
WHERE COALESCE(TRIM(image_file), '') = '';

UPDATE route_steps
SET audio_file = audio_path
WHERE COALESCE(TRIM(audio_file), '') = '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_route_steps_route_step_number
    ON route_steps(route_id, step_number);

CREATE INDEX IF NOT EXISTS idx_route_steps_route_active_step
    ON route_steps(route_id, is_active, step_number);

-- route_news: add normalized key/order/audio/transcript fields.
ALTER TABLE route_news ADD COLUMN news_code TEXT;
ALTER TABLE route_news ADD COLUMN news_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE route_news ADD COLUMN audio_file TEXT;
ALTER TABLE route_news ADD COLUMN transcript_ru TEXT;
ALTER TABLE route_news ADD COLUMN transcript_en TEXT;
ALTER TABLE route_news ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;

UPDATE route_news
SET news_code = printf('news_%d', id)
WHERE COALESCE(TRIM(news_code), '') = '';

UPDATE route_news
SET audio_file = audio_path
WHERE COALESCE(TRIM(audio_file), '') = '';

UPDATE route_news
SET transcript_ru = text
WHERE COALESCE(TRIM(transcript_ru), '') = '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_route_news_route_news_code
    ON route_news(route_id, news_code);

CREATE INDEX IF NOT EXISTS idx_route_news_route_active_order
    ON route_news(route_id, is_active, news_order);

-- route_questions: add block/question-number based shape for block-driven flow.
ALTER TABLE route_questions ADD COLUMN question_block_id INTEGER;
ALTER TABLE route_questions ADD COLUMN question_number INTEGER;
ALTER TABLE route_questions ADD COLUMN question_en TEXT;
ALTER TABLE route_questions ADD COLUMN question_translation_ru TEXT;

UPDATE route_questions
SET question_en = prompt
WHERE COALESCE(TRIM(question_en), '') = '';

UPDATE route_questions
SET question_number = (
    SELECT COUNT(*)
    FROM route_questions AS rq2
    WHERE rq2.route_id = route_questions.route_id
      AND rq2.id <= route_questions.id
)
WHERE question_number IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_route_questions_route_block_question
    ON route_questions(route_id, question_block_id, question_number);

CREATE INDEX IF NOT EXISTS idx_route_questions_route_block_active
    ON route_questions(route_id, question_block_id, is_active, question_number);

-- route_question_blocks: one route has multiple selectable question blocks.
CREATE TABLE IF NOT EXISTS route_question_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    block_code TEXT NOT NULL,
    block_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(route_id, block_code),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_route_question_blocks_route_active_order
    ON route_question_blocks(route_id, is_active, block_order);

-- route_user_state: runtime state for current route flow/toggles/navigation.
CREATE TABLE IF NOT EXISTS route_user_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    phase TEXT NOT NULL,
    current_step_number INTEGER,
    selected_news_id INTEGER,
    selected_block_id INTEGER,
    current_question_number INTEGER,
    show_transcript INTEGER NOT NULL DEFAULT 0,
    show_pilot_answer INTEGER NOT NULL DEFAULT 0,
    show_ru_translation INTEGER NOT NULL DEFAULT 0,
    entry_mode TEXT NOT NULL DEFAULT 'full',
    is_active_session INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, route_id),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_route_user_state_user_active
    ON route_user_state(user_id, is_active_session);

CREATE INDEX IF NOT EXISTS idx_route_user_state_route
    ON route_user_state(route_id);

COMMIT;

PRAGMA foreign_keys = ON;
