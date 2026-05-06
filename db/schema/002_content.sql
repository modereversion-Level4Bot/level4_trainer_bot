PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS grammar_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grammar_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    correct_answer TEXT,
    options_json TEXT,
    explanation TEXT,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES grammar_topics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    prompt TEXT NOT NULL,
    expected_answer TEXT,
    category TEXT,
    difficulty TEXT,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
