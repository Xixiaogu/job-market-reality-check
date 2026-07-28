# Job Market Reality Check Skill

A reusable Agent Skill that turns collected job postings, a real user profile, and project evidence into a transparent application queue and short action plan.

## Outputs

- market-sample summary;
- recurring skill demand;
- hard-condition checks;
- `apply_now`, `stretch`, `prepare_first`, and `defer` tiers;
- evidence mapping from projects to requirements;
- skill-gap priorities;
- calibration metrics when human labels are supplied.

## Install

### Project-level Codex / Agent Skills clients

Copy this folder to:

```text
.agents/skills/job-market-reality-check
```

### ChatGPT Skills upload

Upload the packaged skill ZIP in a workspace where Skills upload is enabled.

## Portable script

```bash
python scripts/analyze_job_market.py \
  --jobs examples/sample_jobs.json \
  --profile examples/sample_profile.json \
  --labels examples/sample_labels.json \
  --output-dir output
```

## Test

```bash
python tests/test_skill_workflow.py
```

## Relationship to the local demo

The browser extension, FastAPI service, SQLite database, and decision dashboard are an optional engineering demo and data-collection layer. The skill does not require the desktop installer.
