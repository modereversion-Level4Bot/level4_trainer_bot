PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS deleted_account_cleanup (
    telegram_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, chat_id)
);
