PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    departure_icao TEXT,
    arrival_icao TEXT,
    difficulty TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS route_briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    title TEXT,
    text TEXT NOT NULL,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS route_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    step_no INTEGER NOT NULL,
    title TEXT,
    text TEXT NOT NULL,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    UNIQUE(route_id, step_no),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS route_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    news_date TEXT,
    title TEXT,
    text TEXT NOT NULL,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS route_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    expected_answer TEXT,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);
