PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS daily_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tip_date TEXT NOT NULL,
    title TEXT,
    text TEXT NOT NULL,
    image_required INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    audio_required INTEGER NOT NULL DEFAULT 0,
    audio_path TEXT,
    voice_required INTEGER NOT NULL DEFAULT 0,
    voice_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tip_date)
);

CREATE TABLE IF NOT EXISTS training_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder_code TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL,
    target_hour INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_daily_tip_seen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tip_id INTEGER NOT NULL,
    seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tip_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tip_id) REFERENCES daily_tips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_training_reminder_seen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reminder_id INTEGER NOT NULL,
    seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, reminder_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reminder_id) REFERENCES training_reminders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pending_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    scheduled_at TEXT,
    delivered_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
