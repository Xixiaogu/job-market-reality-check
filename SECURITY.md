# Security Policy

## Supported versions

Security fixes are currently evaluated for:

- Desktop `v1.0.7`
- Agent Skill `v0.1.x`

Older prototypes and research scripts are not supported releases.

## Reporting a vulnerability

Please do not publish tokens, personal profiles, job databases or exploit details in a public issue.

Use the repository's **Security** tab and choose **Report a vulnerability** when private vulnerability reporting is available. Include:

- the affected version or commit;
- the smallest reproducible example;
- expected and observed behavior;
- whether local data, the API token or another trust boundary is affected.

Remove real job data, names, contact details and local filesystem paths from the report. If private reporting is unavailable, open a minimal public issue requesting a private contact channel without disclosing the vulnerability.

## Security model

- The API is designed to bind only to `127.0.0.1`.
- Protected endpoints require the local `X-Job-Market-Token`.
- The browser extension is restricted to supported job pages and loopback API origins.
- The Agent Skill is read-only and rejects non-loopback API addresses.
- No telemetry or cloud synchronization is included.

The local machine, browser profile and operating-system user account are trusted boundaries. This project has not completed an independent security audit.
