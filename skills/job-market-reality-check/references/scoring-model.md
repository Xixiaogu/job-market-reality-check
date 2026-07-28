# Transparent scoring model

## Dimensions

### Skill match: 0–100

Each required skill is matched against the user's normalized skill inventory.

Evidence multipliers:

- 了解: 0.35
- 基础: 0.55
- 熟练: 0.80
- 可独立完成项目: 1.00

### Project evidence: 0–100

Measures whether at least one project demonstrates multiple required skills and contains a concrete evidence statement.

### Opportunity value: 0–100

Uses only explicit preferences:

- target-title similarity;
- preferred location;
- acceptable employment type;
- stated salary floor when parseable.

### Priority

```text
priority =
  0.50 * skill_match
+ 0.20 * project_evidence
+ 0.30 * opportunity_value
- hard_conflict_penalty
```

Clamp to 0–100.

## Tiers

- hard conflict: `defer`
- priority >= 75 and no more than one material gap: `apply_now`
- priority >= 60: `stretch`
- priority >= 45: `prepare_first`
- otherwise: `defer`

In an action queue, group by tier first and score within each tier.

## Calibration

Tier order:

```text
defer < prepare_first < stretch < apply_now
```

Adjacent agreement means predicted and labeled tiers differ by at most one position. Calibration labels are not a held-out benchmark unless a separate evaluation set exists.
