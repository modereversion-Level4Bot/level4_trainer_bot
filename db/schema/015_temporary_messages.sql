BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS temporary_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    message_type TEXT NOT NULL,
    scope TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_temporary_messages_user_id
    ON temporary_messages(user_id);

CREATE INDEX IF NOT EXISTS idx_temporary_messages_feature
    ON temporary_messages(feature);

CREATE INDEX IF NOT EXISTS idx_temporary_messages_user_feature
    ON temporary_messages(user_id, feature);

CREATE INDEX IF NOT EXISTS idx_temporary_messages_chat_message
    ON temporary_messages(chat_id, message_id);

COMMIT;
