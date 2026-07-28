---
name: job-market-reality-check
description: >
  Analyze a user's collected job postings against their real skills, projects, constraints, and goals.
  Use this skill for job-market reality checks, application prioritization, skill-gap analysis,
  four-tier application decisions (apply now, stretch, prepare first, defer), evidence mapping,
  and short job-search action plans based on CSV, JSON, JSONL, pasted, exported, or locally stored job data.
  Do not use it merely to rewrite one resume bullet or to search live openings without market analysis.
license: MIT
compatibility: Works in ChatGPT Skills, Codex, and Agent Skills-compatible clients. Bundled scripts require Python 3.10+ and use only the standard library.
metadata:
  author: job-market-reality-check
  version: "1.0.0"
---

# Job Market Reality Check

Turn collected job postings plus a user's real evidence into a transparent application plan.

## Required outcome

Answer these questions:

1. What role directions and recurring requirements are actually present in the supplied sample?
2. Which jobs should the user apply to now, stretch for, prepare for first, or defer?
3. Which hard requirements are satisfied, uncertain, or conflicting?
4. Which skills are backed by projects, coursework, repositories, or work samples?
5. What should the user change in their resume, portfolio, and next two weeks of work?

Never present the result as an offer probability, hiring probability, or trained machine-learning prediction.

## Inputs

Use files already supplied by the user whenever possible. Accept:

- job data in CSV, JSON, JSONL, pasted text, or a local-demo export;
- a profile JSON, resume, project descriptions, or conversation context;
- optional human labels: `apply_now`, `stretch`, `prepare_first`, `defer`;
- optional constraints: target roles, city, internship/full-time, graduation year, salary floor, and unavailable work arrangements.

Read `references/input-schema.md` when converting messy inputs.
Read `references/scoring-model.md` before changing weights or thresholds.
Read `references/output-contract.md` before drafting the final report.

## Workflow

### 1. Confirm the decision question

Infer obvious context. Ask only for missing information that materially changes the result:

- target role or role family;
- internship versus full-time;
- acceptable locations;
- education and graduation timing;
- actual skills and project evidence;
- non-negotiable constraints.

Do not force the user through a long questionnaire. State assumptions explicitly.

### 2. Qualify the market sample

Report:

- number of usable postings;
- source and date range when available;
- duplicates and incomplete rows;
- missing salary, education, experience, and skill fields;
- why the sample may not represent the whole market.

Never generalize from a small sample to the entire industry without qualification.

### 3. Normalize jobs and evidence

Prefer the bundled script for repeatability:

```bash
python scripts/analyze_job_market.py \
  --jobs <jobs.csv|jobs.json|jobs.jsonl> \
  --profile <profile.json> \
  --output-dir <output-directory>
```

Add `--labels <labels.json>` when calibration labels exist.

The script creates:

- `normalized_jobs.json`;
- `decision_results.json`;
- `report.md`.

When scripts cannot run, reproduce the same logic manually and disclose that the result is manual.

### 4. Separate hard requirements from soft preferences

Classify each important requirement as:

- `satisfied`;
- `uncertain`;
- `conflict`;
- `not_stated`.

Hard conflicts override a high soft-match score. Do not silently assume graduation-year eligibility, work authorization, degree equivalence, experience, or on-site availability.

### 5. Score with evidence

Keep these dimensions separate:

- skill match;
- project evidence;
- hard-condition status;
- opportunity value;
- preparation cost;
- final application priority.

A skill name without evidence is weaker than a project demonstrating it. Do not invent precision; whole-number scores are enough.

### 6. Apply four action tiers

Use:

- `apply_now`: submit with current materials;
- `stretch`: worthwhile despite a limited gap;
- `prepare_first`: promising, but a specific skill or material gap should be addressed first;
- `defer`: hard conflict, low relevance, or poor opportunity value.

Explain the main reason for every top recommendation and every surprising deferral.

### 7. Calibrate honestly

When human labels are supplied:

- compute exact agreement;
- compute adjacent-tier agreement;
- inspect the largest disagreements;
- adjust thresholds only when the pattern is coherent;
- call it rule calibration, not model training.

Never optimize to a tiny label set and claim general predictive accuracy.

### 8. Produce an action report

Follow `assets/report-template.md`.

Prioritize:

1. the next jobs to act on;
2. the evidence to emphasize;
3. the smallest high-value gaps to close;
4. the limits of the data.

Respond in the user's language.

## Local demo integration

When the repository's FastAPI demo is available:

- use it as an optional collector and visualization layer;
- do not require the Windows installer for skill execution;
- never expose `api_token.txt`, the SQLite database, personal profile data, or real exports;
- treat the browser extension as optional, not part of the minimum skill runtime.

## Gotchas

- High salary does not automatically mean high opportunity value.
- Keyword overlap is not evidence of competence.
- `Python/R` and similar alternatives must not be treated as requiring both.
- A title can conflict with the body; inspect the full description.
- A high-scoring job can still be `stretch` when evidence is weak.
- A lower-scoring job can be `apply_now` when preparation cost is near zero.
- Missing information is `uncertain`, not automatically satisfied.
- Do not advise mass applying without ranking and batching.

## Final quality checks

Before finishing, verify:

- all counts reconcile;
- no private token, database path, or personal identifier is exposed;
- every top action has a reason;
- every hard conflict is visible;
- scores and tiers are internally consistent;
- recommendations are grounded in supplied data;
- sample limitations are stated;
- the user receives a concrete next action, not only analysis.
