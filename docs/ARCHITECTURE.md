# Architecture and module map

This document describes the repository as it currently exists. It is a navigation aid, not a promise that every module is enabled or every feature has complete automated coverage.

## Runtime entry point

- `Procfile` starts `python bot.py`.
- `bot.py` is the application entry point. It imports the main configuration and database helpers, registers the primary Telegram handlers, and imports the active feature modules listed below.
- `config.py` creates the Telegram bot client and holds translations, ranks, administrator identifiers, channel defaults, and other application configuration.
- `database.py` owns SQLAlchemy/PostgreSQL access, schema initialization, persistent state stores, purchase/payment helpers, and backup/restore operations.
- `utils.py` contains shared Telegram, moderation, channel-publishing, and formatting helpers.
- `keyboards.py` builds Telegram reply and inline keyboards.
- `shop_ui.py` contains shop presentation helpers.

## Feature modules loaded by bot.py

The current `bot.py` imports `bot2.py`, `bot3.py`, `bot4.py`, `bot5.py`, `bot6.py`, `bot7.py`, `bot8.py`, and `bot9.py`. These modules register or provide feature handlers used by the main application. Review their registration behavior before moving code or changing import order.

## Module requiring maintainer confirmation

- `bot10.py` describes itself as a premium visual-experience module and its header says to import it from `bot.py`.
- The current `bot.py` does not import `bot10.py`.
- Treat `bot10.py` as dormant/unverified until a maintainer confirms that its handlers and background behavior should be enabled. Do not assume its features are currently available to users.

## Persistent data

PostgreSQL, configured through `DATABASE_URL`, is the durable source of truth. The JSON-named stores in `database.py` are compatibility interfaces backed by PostgreSQL; local JSON mirrors are not a substitute for a database backup. Read [BACKUP_AND_MIGRATION.md](../BACKUP_AND_MIGRATION.md) before changing persistence or restore behavior.

## Configuration

- `API_TOKEN` and `DATABASE_URL` are required.
- A local `.env` file is loaded by `python-dotenv` from `config.py`.
- Hosting environments should provide variables through their secret/environment settings.
- Administrator identifiers and channel defaults are currently defined in `config.py`; review and replace these before deploying a separate instance. Never copy another operator's private configuration.

## Tests and known coverage limits

- `tests/test_channel_broadcasting.py` covers selected channel broadcasting behavior.
- GitHub Actions compiles Python files, runs the unit test suite, and runs a PostgreSQL smoke test for selected persistence, purchase, payment-idempotency, and backup/restore paths.
- Telegram API interactions, every admin workflow, all payment edge cases, and a real hosting deployment are not comprehensively covered. Add focused tests when changing these areas.

## Safe contribution rule

Keep changes narrow. Preserve existing bot behavior unless a change explicitly intends to alter it. Do not delete numbered feature modules, change database schemas, or activate dormant modules without tracing their callers and adding regression tests.
