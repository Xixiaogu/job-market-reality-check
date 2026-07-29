# Brief workflow

Use this workflow for questions such as:

- “根据我现在的数据，我的求职情况怎么样？”
- “我现在最应该做什么？”
- “给我一份当前求职简报。”

## Input

Call `LocalAPIClient.brief_context()` or run:

```bash
python scripts/local_api_client.py brief
```

Use only the returned snapshot. Do not combine it with an older decision run or rescore its jobs.

## Read in this order

1. Confirm `health.ok`.
2. Record contract, service, engine, decision-run, and generated-at metadata.
3. Check profile onboarding and evidence counts.
4. Reconcile `health.job_count`, management totals, decision job count, and pending queue count.
5. Inspect action-group counts and the complete pending queue.
6. Identify repeated strengths, gaps, hard conflicts, and information risks.
7. Select one best next action.

## Route insufficient states

- No jobs: recommend collecting a focused initial sample.
- Incomplete profile: name the one missing profile or evidence field that most limits decisions.
- No pending jobs: explain whether jobs are already in process, closed, archived, or deferred.
- No decision run: report that local decisions are unavailable; do not fall back to a second scorer.
- Many information risks: lower confidence and prioritize data completion.
- Many high-priority jobs with no action: prioritize a small submission batch.

## Output structure

### Current judgment

State the strongest conclusion in two or three sentences. Include the usable sample and pending-queue size. Qualify sample bias.

### Current funnel

Report:

- total active jobs;
- pending decision jobs;
- counts for `apply_now`, `stretch`, `prepare_first`, and `defer`;
- jobs already in an application or interview process when available.

### Best opportunities

List at most five jobs. Include:

- `job_id`;
- role and company;
- action group and priority;
- main evidence;
- most important risk or unknown;
- suggested action.

Do not rank only by priority score. Preserve hard conflicts and preparation cost.

### Evidence and gaps

Separate:

- strongest direct project evidence;
- transferable evidence;
- recurring real gaps;
- missing information.

Do not transform a missing field into a skill gap.

### Bottleneck

Identify one current bottleneck, such as:

- insufficient sample;
- incomplete profile;
- weak project evidence;
- too many prepare-first jobs;
- high-priority queue without submissions;
- repeated applications without response.

### Next action

Give exactly one best action that can be completed next. Make it specific and bounded.

### Limits

State:

- the data describes a personal collected sample;
- desktop scores are rule-based decision aids, not offer probabilities;
- the brief uses one recorded decision run.

## Confidence

Use:

- high: complete profile, clear evidence, few information risks;
- medium: useful evidence with limited missing fields;
- low: small sample, incomplete profile, stale run, or many unknowns.

Do not express confidence as a fabricated percentage.
