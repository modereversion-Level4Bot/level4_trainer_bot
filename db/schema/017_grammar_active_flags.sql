PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

ALTER TABLE grammar_questions
ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;

UPDATE grammar_questions
SET is_active = 1
WHERE is_active IS NULL;

COMMIT;

PRAGMA foreign_keys = ON;
