PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE grammar_topics_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    topic_number INTEGER NOT NULL UNIQUE,
    topic_type TEXT NOT NULL DEFAULT 'main' CHECK (topic_type IN ('main', 'extra')),
    title_ru TEXT NOT NULL,
    title_en TEXT,
    simple_explanation_ru TEXT NOT NULL,
    simple_explanation_en TEXT,
    detailed_explanation_ru TEXT,
    detailed_explanation_en TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO grammar_topics_new (
    id,
    slug,
    title,
    description,
    sort_order,
    is_active,
    topic_number,
    topic_type,
    title_ru,
    title_en,
    simple_explanation_ru,
    simple_explanation_en,
    detailed_explanation_ru,
    detailed_explanation_en,
    created_at,
    updated_at
)
SELECT
    gt.id,
    COALESCE(NULLIF(TRIM(gt.slug), ''), printf('grammar_%03d', gt.id)),
    COALESCE(
        NULLIF(TRIM(gt.title), ''),
        COALESCE(NULLIF(TRIM(gt.slug), ''), printf('grammar_%03d', gt.id))
    ),
    gt.description,
    CASE
        WHEN COALESCE(gt.sort_order, 0) > 0 THEN gt.sort_order
        ELSE gt.id
    END,
    COALESCE(gt.is_active, 1),
    gt.id,
    'main',
    COALESCE(
        NULLIF(TRIM(gt.title), ''),
        COALESCE(NULLIF(TRIM(gt.slug), ''), printf('grammar_%03d', gt.id))
    ),
    NULL,
    COALESCE(gt.description, ''),
    NULL,
    NULL,
    NULL,
    COALESCE(gt.created_at, CURRENT_TIMESTAMP),
    COALESCE(gt.updated_at, CURRENT_TIMESTAMP)
FROM grammar_topics AS gt;

DROP TABLE grammar_topics;
ALTER TABLE grammar_topics_new RENAME TO grammar_topics;

CREATE INDEX IF NOT EXISTS idx_grammar_topics_topic_type ON grammar_topics(topic_type);
CREATE INDEX IF NOT EXISTS idx_grammar_topics_sort_order ON grammar_topics(sort_order);

CREATE TABLE grammar_questions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    topic_number INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    question_ru TEXT NOT NULL,
    question_en TEXT,
    answer_1_ru TEXT NOT NULL,
    answer_1_en TEXT,
    answer_2_ru TEXT NOT NULL,
    answer_2_en TEXT,
    answer_3_ru TEXT NOT NULL,
    answer_3_en TEXT,
    answer_4_ru TEXT NOT NULL,
    answer_4_en TEXT,
    correct_answer INTEGER NOT NULL CHECK (correct_answer IN (1, 2, 3, 4)),
    options_json TEXT,
    explanation TEXT,
    wrong_explanation_ru TEXT NOT NULL,
    wrong_explanation_en TEXT,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (topic_number, question_number),
    FOREIGN KEY (topic_id) REFERENCES grammar_topics(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_number) REFERENCES grammar_topics(topic_number) ON DELETE CASCADE
);

INSERT INTO grammar_questions_new (
    id,
    topic_id,
    topic_number,
    question_number,
    prompt,
    question_ru,
    question_en,
    answer_1_ru,
    answer_1_en,
    answer_2_ru,
    answer_2_en,
    answer_3_ru,
    answer_3_en,
    answer_4_ru,
    answer_4_en,
    correct_answer,
    options_json,
    explanation,
    wrong_explanation_ru,
    wrong_explanation_en,
    image_required,
    image_path,
    audio_required,
    audio_path,
    voice_required,
    voice_path,
    is_active,
    created_at,
    updated_at
)
SELECT
    gq.id,
    gq.topic_id,
    gt.topic_number,
    (
        SELECT COUNT(*)
        FROM grammar_questions AS gq2
        WHERE gq2.topic_id = gq.topic_id
          AND gq2.id <= gq.id
    ),
    COALESCE(NULLIF(TRIM(gq.prompt), ''), printf('Question %d', gq.id)),
    COALESCE(NULLIF(TRIM(gq.prompt), ''), printf('Question %d', gq.id)),
    NULL,
    '',
    NULL,
    '',
    NULL,
    '',
    NULL,
    '',
    NULL,
    CASE
        WHEN CAST(COALESCE(gq.correct_answer, '') AS INTEGER) BETWEEN 1 AND 4
            THEN CAST(gq.correct_answer AS INTEGER)
        ELSE 1
    END,
    gq.options_json,
    gq.explanation,
    COALESCE(gq.explanation, ''),
    NULL,
    COALESCE(gq.image_required, 0),
    gq.image_path,
    COALESCE(gq.audio_required, 0),
    gq.audio_path,
    COALESCE(gq.voice_required, 0),
    gq.voice_path,
    COALESCE(gq.is_active, 1),
    COALESCE(gq.created_at, CURRENT_TIMESTAMP),
    COALESCE(gq.updated_at, CURRENT_TIMESTAMP)
FROM grammar_questions AS gq
JOIN grammar_topics AS gt ON gt.id = gq.topic_id;

DROP TABLE grammar_questions;
ALTER TABLE grammar_questions_new RENAME TO grammar_questions;

CREATE INDEX IF NOT EXISTS idx_grammar_questions_topic_id ON grammar_questions(topic_id);
CREATE INDEX IF NOT EXISTS idx_grammar_questions_topic_number ON grammar_questions(topic_number);

COMMIT;

PRAGMA foreign_keys = ON;
