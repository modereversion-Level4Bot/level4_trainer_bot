BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS media_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content_key TEXT NOT NULL,
    local_path TEXT NOT NULL,
    file_id TEXT,
    file_unique_id TEXT,
    checksum TEXT,
    status TEXT NOT NULL CHECK (status IN ('ready', 'missing', 'failed', 'outdated', 'skipped')),
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (feature, content_type, content_key)
);

CREATE INDEX IF NOT EXISTS idx_media_assets_feature
    ON media_assets(feature);

CREATE INDEX IF NOT EXISTS idx_media_assets_content_type
    ON media_assets(content_type);

CREATE INDEX IF NOT EXISTS idx_media_assets_status
    ON media_assets(status);

CREATE INDEX IF NOT EXISTS idx_media_assets_feature_content_type
    ON media_assets(feature, content_type);

CREATE INDEX IF NOT EXISTS idx_media_assets_feature_content_type_content_key
    ON media_assets(feature, content_type, content_key);

COMMIT;
