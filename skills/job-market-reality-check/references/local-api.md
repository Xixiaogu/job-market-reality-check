# Local desktop API mode

Use this reference only when the local Job Market desktop service is available.

## Safety boundary

- Connect only to `http://127.0.0.1`, `http://localhost`, or IPv6 loopback.
- Send the Token only in `X-Job-Market-Token`.
- Use `GET` endpoints only.
- Never open `job_market.db`.
- Never use `refresh=true`.
- Never print the Token or local diagnostic paths.
- Treat the desktop decision engine as authoritative; do not compute a second score.

The repository-level frozen contract is `docs/skill-v1-local-api-contract.md`.

## Client commands

Check service availability without loading the Token:

```bash
python scripts/local_api_client.py health
```

Fetch a consistent brief context:

```bash
python scripts/local_api_client.py brief
```

Optional settings:

```bash
python scripts/local_api_client.py \
  --base-url http://127.0.0.1:8765 \
  --token-file <local-token-file> \
  --timeout 10 \
  brief
```

Do not pass the Token value on the command line.

Use `--output` only when the user explicitly asks to save a private snapshot.

## Brief context

The client returns:

- `contract_version`;
- `generated_at`;
- `metadata.service_version`;
- `metadata.engine_version`;
- `metadata.decision_run_id`;
- `metadata.decision_created_at`;
- sanitized health data;
- management counts;
- the full profile needed for evidence checks;
- the decision summary;
- the complete paginated pending queue.

The client rejects:

- non-local hosts;
- missing or rejected Tokens;
- malformed JSON;
- missing required fields;
- changing totals during pagination;
- different decision runs across pages or summary.

## Read-only method mapping

| Task | Client method |
|---|---|
| Health | `health()` |
| All managed jobs | `jobs()` |
| Job facts | `job(job_id)` |
| Status history | `job_history(job_id)` |
| Profile | `profile()` |
| Decision summary | `decision_summary()` |
| Complete decision queue | `decision_jobs()` |
| One decision | `decision_job(job_id)` |
| Calibration quality | `decision_calibration()` |
| Brief snapshot | `brief_context()` |

## Error behavior

- Connection failure: ask the user to start the desktop app.
- Authentication failure: ask the user to re-pair; never request the Token value in chat.
- `404`: state that the job or current decision result is absent.
- `422`: report an incompatible parameter or strategy.
- Contract error: stop the workflow and report an API compatibility problem.
