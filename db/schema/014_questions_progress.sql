PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP TABLE IF EXISTS exam_question_progress_old;
ALTER TABLE exam_question_progress RENAME TO exam_question_progress_old;

CREATE TABLE exam_question_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level INTEGER NOT NULL CHECK (level IN (4, 5)),
    question_number INTEGER NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, level, question_number),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO exam_question_progress (
    user_id,
    level,
    question_number,
    completed_at
)
SELECT
    eqp.user_id,
    eq.level,
    eq.question_number,
    COALESCE(eqp.last_answer_at, CURRENT_TIMESTAMP) AS completed_at
FROM exam_question_progress_old AS eqp
JOIN exam_questions AS eq ON eq.id = eqp.question_id
WHERE COALESCE(eqp.attempts, 0) > 0
   OR COALESCE(eqp.is_correct, 0) = 1;

DROP TABLE IF EXISTS exam_question_progress_old;

CREATE INDEX IF NOT EXISTS idx_exam_question_progress_user_id
    ON exam_question_progress(user_id);

CREATE INDEX IF NOT EXISTS idx_exam_question_progress_user_level
    ON exam_question_progress(user_id, level);

CREATE TABLE IF NOT EXISTS exam_question_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level INTEGER NOT NULL CHECK (level IN (4, 5)),
    current_question_number INTEGER,
    last_audio_message_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, level),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exam_question_state_user_id
    ON exam_question_state(user_id);

COMMIT;

PRAGMA foreign_keys = ON;
