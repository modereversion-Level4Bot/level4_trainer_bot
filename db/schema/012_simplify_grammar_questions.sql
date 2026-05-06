PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP TABLE IF EXISTS grammar_questions_new;

CREATE TABLE grammar_questions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_number INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer_1 TEXT NOT NULL,
    answer_2 TEXT NOT NULL,
    answer_3 TEXT NOT NULL,
    correct_answer INTEGER NOT NULL CHECK (correct_answer IN (1, 2, 3)),
    wrong_explanation_ru TEXT NOT NULL,
    wrong_explanation_en TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (topic_number, question_number),
    FOREIGN KEY (topic_number) REFERENCES grammar_topics(topic_number) ON DELETE CASCADE
);

DROP TABLE IF EXISTS grammar_questions;
ALTER TABLE grammar_questions_new RENAME TO grammar_questions;

CREATE INDEX IF NOT EXISTS idx_grammar_questions_topic_number
    ON grammar_questions(topic_number);

DELETE FROM grammar_training_sessions;

COMMIT;

PRAGMA foreign_keys = ON;
