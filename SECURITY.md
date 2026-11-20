# Security Policy

## Supported versions

Security fixes are currently intended for the latest version on the default branch. There is no formal long-term support schedule yet.

## Reporting a vulnerability

Please do not publish exploitable vulnerabilities, credentials, bot tokens, database URLs, or private user data in public Issues.

Use GitHub's private vulnerability reporting feature for this repository if it is enabled. Otherwise, contact the repository owner privately through their GitHub profile and include:

- A clear description of the issue.
- Steps to reproduce it safely.
- The potential impact.
- Any suggested mitigation.

Please allow time for investigation and a fix before public disclosure.

## Secret handling

- Keep `.env`, database dumps, and backup files out of Git.
- Rotate any token or credential that may have been exposed.
- Use separate development and production credentials.
- Avoid logging authentication data or personal information.
