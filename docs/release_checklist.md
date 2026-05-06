# Release / Security checklist

Use this checklist before pushing to GitHub, creating archives, or deploying.

## 1) Secrets and sensitive files

- `.env` is local only and is not tracked by git.
- Database/backup artifacts are not tracked (`*.db`, `*.sqlite*`, `backups/`).
- Google credentials files are not tracked (`google_service_account.json`, `credentials.json`, `token.json`, `*service_account*.json`).
- Local secrets folders are not tracked (`secrets/`).

## 2) Environment variables on target server

- `BOT_TOKEN` is set in server environment (not hardcoded in repo).
- `MEDIA_PRELOAD_CHAT_ID` is set in server environment.
- `GOOGLE_SHEET_ID` is set in server environment.
- `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` is set in server environment.

## 2.1) Token separation policy

- Local development uses only a dedicated dev/test bot token.
- Railway uses only the official production token.
- Never run the same `BOT_TOKEN` in two polling processes at the same time.
- If Railway is running with the official token, do not run that same token locally.

## 3) Logging safety

- Project logging does not print raw `BOT_TOKEN`.
- Debug logs from third-party Telegram/HTTP libraries are not enabled in production.

## 4) Content import safety

- `python scripts/import_questions.py` is not run in production without explicit flag:
  `--allow-full-refresh`.
- For safe validation-only checks, use:
  `python scripts/import_questions.py --dry-run`.
- After questions import, run:
  `python scripts/preload_question_audio.py`.
- `media/questions/*.mp3` source files are not committed to GitHub.
- Source audio is stored separately (local backup / cloud storage / Railway volume / agreed storage).

## 4.1) Official Questions audio cache checks (MVP ops)

- Runtime cache source is `media_assets` with:
  - `feature='questions'`
  - `content_type='question_audio'`
- Closure criteria for official preload/cutover:
  - `status='ready'` count = `261`
  - non-empty `file_id` count = `261`
  - official bot audio smoke is successful
- For DB-to-Railway cache transfer use ops scripts:
  - `python scripts/export_question_audio_media_assets.py`
  - `python scripts/import_question_audio_media_assets_from_env.py`
  - `python scripts/diagnose_railway_db.py`
- For Railway variable size limit use chunked gzip variables:
  - `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNKS`
  - `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNK_001`
  - `MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNK_002`
- After any temporary Railway Start Command for diagnostics/import, restore:
  - `python run.py`

## 5) Final pre-release check

- Run baseline checks:
  - `python -m compileall .`
  - `python scripts/init_db.py`
  - `python scripts/smoke_check.py`
- Confirm Telegram smoke:
  onboarding, settings, grammar, questions, clean-chat, one-main-UI-message.
