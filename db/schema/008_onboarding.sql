PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user_onboarding_state (
    user_id INTEGER PRIMARY KEY,
    interface_language TEXT CHECK (interface_language IN ('ru', 'en')),
    timezone TEXT NOT NULL DEFAULT 'UTC',
    daily_tips_enabled INTEGER NOT NULL DEFAULT 1,
    daily_tip_time TEXT,
    training_reminders_enabled INTEGER NOT NULL DEFAULT 1,
    training_reminder_time TEXT,
    sound_enabled INTEGER NOT NULL DEFAULT 1,
    onboarding_completed INTEGER NOT NULL DEFAULT 0,
    onboarding_step TEXT NOT NULL DEFAULT 'language_select',
    waiting_state TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
