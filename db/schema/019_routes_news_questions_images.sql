PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

ALTER TABLE route_news ADD COLUMN image_file TEXT;
UPDATE route_news
SET image_file = image_path
WHERE COALESCE(TRIM(image_file), '') = ''
  AND COALESCE(TRIM(image_path), '') <> '';

ALTER TABLE route_questions ADD COLUMN image_file TEXT;
UPDATE route_questions
SET image_file = image_path
WHERE COALESCE(TRIM(image_file), '') = ''
  AND COALESCE(TRIM(image_path), '') <> '';

COMMIT;
PRAGMA foreign_keys = ON;
