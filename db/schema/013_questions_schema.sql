PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP TABLE IF EXISTS exam_questions_new;

CREATE TABLE exam_questions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL CHECK (level IN (4, 5)),
    question_number INTEGER NOT NULL,
    question_en TEXT NOT NULL,
    audio_file TEXT,
    question_translation_ru TEXT,
    sample_answer_en TEXT,
    sample_answer_translation_ru TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (level, question_number)
);

INSERT INTO exam_questions_new (
    id,
    level,
    question_number,
    question_en,
    audio_file,
    question_translation_ru,
    sample_answer_en,
    sample_answer_translation_ru,
    is_active,
    created_at,
    updated_at
)
SELECT
    eq.id,
    CASE
        WHEN TRIM(COALESCE(eq.difficulty, '')) = '5' THEN 5
        ELSE 4
    END AS level,
    ROW_NUMBER() OVER (
        PARTITION BY CASE
            WHEN TRIM(COALESCE(eq.difficulty, '')) = '5' THEN 5
            ELSE 4
        END
        ORDER BY eq.id
    ) AS question_number,
    COALESCE(NULLIF(TRIM(eq.prompt), ''), printf('Question %d', eq.id)) AS question_en,
    NULLIF(TRIM(COALESCE(eq.audio_path, '')), '') AS audio_file,
    NULL AS question_translation_ru,
    NULLIF(TRIM(COALESCE(eq.expected_answer, '')), '') AS sample_answer_en,
    NULL AS sample_answer_translation_ru,
    COALESCE(eq.is_active, 1) AS is_active,
    COALESCE(eq.created_at, CURRENT_TIMESTAMP) AS created_at,
    COALESCE(eq.updated_at, CURRENT_TIMESTAMP) AS updated_at
FROM exam_questions AS eq
ORDER BY eq.id;

DROP TABLE IF EXISTS exam_questions;
ALTER TABLE exam_questions_new RENAME TO exam_questions;

CREATE INDEX IF NOT EXISTS idx_exam_questions_level
    ON exam_questions(level);

CREATE INDEX IF NOT EXISTS idx_exam_questions_level_question_number
    ON exam_questions(level, question_number);

COMMIT;

PRAGMA foreign_keys = ON;
