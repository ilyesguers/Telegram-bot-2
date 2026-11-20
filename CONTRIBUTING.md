# Contributing

Thank you for considering a contribution to Telegram Bot 2.

## Before you start

- Search existing Issues and Pull Requests to avoid duplicate work.
- For large changes or behavior changes, open an Issue first to discuss the approach.
- Keep the existing bot behavior unless the change intentionally fixes a documented bug.
- Do not include secrets, personal user data, production backups, or real payment information.

## Development setup

1. Use Python 3.11.
2. Create a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Configure a test Telegram bot token and a disposable PostgreSQL database using `.env`.
5. Never develop against the production database.

## Pull requests

A good pull request should:

- Explain the problem and the proposed solution.
- Keep changes focused and avoid unrelated refactoring.
- Include tests for bug fixes and new behavior where practical.
- Update documentation when setup, configuration, or behavior changes.
- Pass the repository's GitHub Actions checks.
- Avoid committing generated files, credentials, local databases, or backups.

## Code style and safety

- Prefer clear names and small, understandable functions.
- Handle Telegram API and database failures explicitly.
- Validate administrator-only actions and payment-related inputs.
- Make payment processing idempotent where applicable.
- Do not log tokens, database URLs, or private user information.

By submitting a contribution, you confirm that you have the right to submit it under this repository's MIT License.
