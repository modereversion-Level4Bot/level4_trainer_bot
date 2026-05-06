PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS grammar_training_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    topic_number INTEGER NOT NULL,
    topic_type TEXT NOT NULL CHECK (topic_type IN ('main', 'extra')),
    source_page INTEGER NOT NULL DEFAULT 1,
    question_numbers_json TEXT NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    total_questions INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    wrong_count INTEGER NOT NULL DEFAULT 0,
    is_finished INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_number) REFERENCES grammar_topics(topic_number) ON DELETE CASCADE
);
