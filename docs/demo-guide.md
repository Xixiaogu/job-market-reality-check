# Three-minute portfolio demo

This script uses fictional data and the **Windows Acrylic** appearance. Acrylic is deliberately selected instead of the default Standard Light theme; unsupported systems fall back safely.

## Before the call

1. Install or unzip desktop v1.0.7.
2. Generate or import only fictional demo data.
3. Open **Extensions & Settings**, select **Windows Acrylic**, then restart.
4. Confirm no real company, recruiter, URL, profile, token or local path is visible.
5. Open **Decision Center** and keep one strong `apply_now`, one `stretch` and one `prepare_first` example ready.

## Demo flow

### 0:00–0:30 — State the problem

“Saving job links is easy; deciding what deserves limited application time is harder. This local-first system connects job evidence, my actual project evidence and explicit constraints.”

### 0:30–1:05 — Capture one posting

Open a fictional or permitted test job page and trigger the extension manually. Show that the result is sent only to the localhost API and deduplicated in SQLite.

### 1:05–1:35 — Show the evidence model

Open the candidate profile. Point out skills, project evidence, location and availability. Explain that missing evidence stays unknown instead of being invented.

### 1:35–2:20 — Explain one decision

Open Decision Center and compare:

- matching evidence;
- opportunity value;
- preparation cost;
- hard constraints and information risk;
- the resulting four-tier action group.

Say explicitly: “This is a transparent prioritization heuristic, not an offer-probability model.”

### 2:20–2:50 — Show the Skill boundary

Run:

```powershell
python .\skills\job-market-reality-check\scripts\local_api_client.py brief
```

Explain that the Skill reads the frozen API, checks decision-run consistency and produces a brief without opening SQLite or writing application state.

### 2:50–3:00 — Close with engineering evidence

Show the CI badge and the synthetic-data workflow. Mention that the unified baseline covers offline logic, the API, desktop mode and Skill workflows, while packaged ZIP and installer smoke tests are release-gate checks.

## Screenshot checklist

- Use Windows Acrylic, not Standard Light.
- Use a 16:9 window with the full left navigation visible.
- Keep the app title and Decision Center heading visible.
- Show at least two distinct action groups.
- Use only records created by `scripts/create_ci_fixture.py`.
- Crop browser chrome when possible.
- Inspect the image at full resolution before committing it.
