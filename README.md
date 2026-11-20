# Telegram Bot 2

A feature-rich Telegram bot built with Python, pyTelegramBotAPI, and PostgreSQL. The project combines community, shop, and administration workflows in one bot.

> **Project status:** Active development. Some features and deployment paths are still being tested. Please report bugs through GitHub Issues rather than assuming every feature is production-ready.

## Features

The current codebase includes modules for:

- User registration, profiles, points, ranks, and quests.
- Product/key shop workflows and configurable prices.
- Telegram Stars purchase/conversion handling.
- Giveaways and claim verification.
- CAPTCHA and anti-spam checks.
- Support tickets and administrator workflows.
- Channel announcements and promotional broadcasts.
- PostgreSQL-backed persistent data.
- Backup and restore helpers for moving the database between hosts.

Feature availability may depend on the bot's configuration and administrator setup.

## Requirements

- Python 3.11 (the current CI workflow uses Python 3.11).
- PostgreSQL.
- A Telegram bot token created with [@BotFather](https://t.me/BotFather).

## Run locally

1. Clone the repository:

   ```bash
   git clone https://github.com/ilyesguers/Telegram-bot-2.git
   cd Telegram-bot-2
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows PowerShell
   .venv\\Scripts\\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure environment variables. Copy `.env.example` to `.env` and set real values. Do not commit `.env`.

   | Variable | Required | Description |
   | --- | --- | --- |
   | `API_TOKEN` | Yes | Telegram bot token from BotFather. |
   | `DATABASE_URL` | Yes | PostgreSQL connection URL. |

   The application also has administrator and channel settings in its configuration module. Review those settings before deploying your own instance.

5. Start the bot:

   ```bash
   python bot.py
   ```

The first startup initializes the database schema. Use a dedicated test bot and test database while evaluating the project.

## Deploy on Railway

1. Create a Railway project and add a PostgreSQL service.
2. Deploy this repository as a service.
3. Set `API_TOKEN` to the token for your own Telegram bot.
4. Set `DATABASE_URL` using the PostgreSQL connection variable provided by Railway. Ensure it is available to the bot service.
5. The repository's `Procfile` starts the application with `python bot.py`.
6. Check deployment logs and test core flows with a test account before inviting users.

Never paste bot tokens, database URLs, backup files, or real user data into GitHub Issues or public logs.

## Tests and validation

The repository includes a GitHub Actions validation workflow and a test for channel broadcasting. The CI workflow also runs a PostgreSQL smoke test for selected persistence, purchase, payment-idempotency, and backup/restore paths.

Run the available unit test locally with:

```bash
python -m unittest discover -s tests -v
```

Not every bot workflow is covered by automated tests yet. A passing CI run is not a guarantee that Telegram API interactions, payment flows, or a Railway deployment are fully verified.

## Backups and migration

Read [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md) before moving production data. Backups can contain sensitive user and shop information. Store them securely outside the repository and test restores against a disposable database first.

## Contributing

Bug reports, documentation improvements, and tested code contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Please do not submit real tokens, user identifiers, payment details, or production database dumps.

## Security

If you discover a vulnerability, follow [SECURITY.md](SECURITY.md). Do not disclose exploitable issues or secrets in public issues.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
