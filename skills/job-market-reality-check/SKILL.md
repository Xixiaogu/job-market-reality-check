---
name: job-market-reality-check
description: Analyze collected job postings against a user's real skills, projects, constraints, and goals. Use for job-market reality checks, evidence-based application prioritization, four-tier decisions, skill-gap analysis, job explanations, comparisons, and short action plans from the local Job Market desktop API or supplied CSV, JSON, JSONL, exports, resumes, and profile data. Do not use only to rewrite one resume bullet or to search live openings without analyzing a job sample.
---

# Job Market Reality Check

Turn collected job facts and real user evidence into a transparent application decision.

Never describe a score as an offer probability, hiring probability, or trained prediction.

## Select the data mode

Prefer one source of truth for each run.

### Local desktop API mode

Use this mode when the Job Market desktop service or repository is available.

1. Read `references/local-api.md`.
2. Use `scripts/local_api_client.py`; never open SQLite directly.
3. Treat desktop decision results as authoritative. Do not run the portable scoring model over the same jobs.
4. Keep the first integration read-only. Do not call `POST`, `PUT`, `PATCH`, or `DELETE`.
5. For a current-state brief, read `references/brief-workflow.md`.

The API client only sends credentials to localhost and automatically checks pagination, required fields, and decision-run consistency.

### Portable file mode

Use this mode when the user supplies files, pasted postings, or an export without the desktop service.

1. Read `references/input-schema.md` when normalizing inputs.
2. Read `references/scoring-model.md` before changing weights or thresholds.
3. Run:

```bash
python scripts/analyze_job_market.py \
  --jobs <jobs.csv|jobs.json|jobs.jsonl> \
  --profile <profile.json> \
  --output-dir <output-directory>
```

Add `--labels <labels.json>` when human calibration labels exist.

The script creates `normalized_jobs.json`, `decision_results.json`, and `report.md`.

## Apply the evidence standard

Separate:

- direct evidence;
- transferable evidence;
- inference;
- unknown information;
- real conflicts.

Treat a skill name without project, coursework, repository, or work-sample evidence as weaker than demonstrated competence. Treat missing information as unknown, not satisfied. Never invent experience, metrics, education equivalence, work authorization, availability, or graduation eligibility.

Keep these dimensions distinct:

- skill match;
- project evidence;
- hard-condition status;
- opportunity value;
- preparation cost;
- final application priority.

Use the existing four action groups:

- `apply_now`: submit with current materials;
- `stretch`: worthwhile despite a limited gap;
- `prepare_first`: close one specific evidence or material gap first;
- `defer`: hard conflict, low relevance, or poor opportunity value.

Explain every top recommendation and every surprising deferral.

## Qualify the sample

Report:

- usable posting count;
- source and date range when available;
- duplicates and incomplete rows;
- important missing fields;
- why the sample may not represent the whole market.

Do not generalize from a personal collection to an entire industry.

## Produce the result

Read `references/output-contract.md` before drafting a full file-mode report. Follow `assets/report-template.md` when creating a persistent report.

Prioritize:

1. the next jobs to act on;
2. the evidence to emphasize;
3. the smallest high-value gaps to close;
4. one best next action;
5. the limits of the data.

Respond in the user's language.

## Protect local data

- Never reveal the API Token or its value.
- Do not expose database, user-data, project-root, or log paths in the result.
- Do not persist an API snapshot unless the user explicitly asks for an export.
- Do not include unnecessary personal profile fields in a shared report.
- Do not advise mass applying, automatic messaging, or bypassing platform restrictions.

## Final checks

Verify:

- counts reconcile;
- all compared jobs use one decision run;
- every top action has a reason;
- hard conflicts and unknowns remain visible;
- API-mode results were not rescored;
- no secret or private path appears;
- the user receives one concrete next action.
