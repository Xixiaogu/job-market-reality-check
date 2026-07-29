# Test suites

The tests are grouped by the environment they require, rather than by the
development phase in which they were added.

| Directory | Purpose | Service required |
|---|---|---|
| `contracts/` | HTML, route, extension, desktop-shell and appearance contracts | No |
| `offline/` | SQLite, profile, calibration and decision-engine behavior | No |
| `api/development/` | Integration against an isolated development-mode API | Yes |
| `api/desktop/` | Desktop-mode status, token and bundled-extension behavior | Yes |
| `release/` | Portable package and installer smoke tests | Packaged artifacts |
| `support/` | Shared repository paths and test helpers | No |

The Skill keeps its own tests under
`skills/job-market-reality-check/tests/` because it is independently
distributable.

## Run the CI baseline

From the repository root, create a fictional database:

```powershell
python .\scripts\create_ci_fixture.py `
  --output .build\ci-fixture\job_market.db
```

Then run the same 30 test groups used by GitHub Actions:

```powershell
$python = (Get-Command python.exe).Source
.\scripts\test.ps1 `
  -Version 1.0.7 `
  -PythonPath $python `
  -SourceDatabasePath .build\ci-fixture\job_market.db `
  -SkipPackaged `
  -SkipInstaller
```

Omit `-SkipPackaged` and `-SkipInstaller` to run the full 32-group release
gate after the v1.0.7 artifacts have been built.

The runner discovers `test_*.py` files in each category automatically.
New tests should use behavior-based names and must not depend on a personal
database, browser profile, token or network service.
