# Privacy

Job Market Reality Check is local-first software. It does not include telemetry, analytics SDKs, cloud synchronization or an account service.

## Data stored locally

Desktop mode stores the following under `%LOCALAPPDATA%\JobMarketDecisionSystem`:

- the SQLite job and profile database;
- a local API token;
- application logs;
- user-created exports and backups.

The repository and release packages do not include the maintainer's database, token, browser profile, logs, exports or personal profile.

## Browser extension

The extension reads a supported job-detail page only after user action. Captured fields are sent to `http://127.0.0.1:8765`; the extension is not designed to send job data to a remote service. It does not bypass login, CAPTCHA or access controls.

Users are responsible for the recruitment platform's terms, the rights attached to collected content and applicable privacy law. Do not redistribute job descriptions or personal recruiter information without permission.

## Agent Skill

Skill v0.1.0 can read the documented local API or files explicitly supplied by the user. It must not print the API token, local database path or hidden personal data. It cannot submit applications, contact recruiters or modify desktop records.

## Removing data

Uninstalling the application intentionally preserves user data. To remove it permanently, close the application, back up anything needed, then delete the Job Market Decision System user-data directory through Windows. This action cannot be undone.
