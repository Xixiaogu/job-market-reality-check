# Contributing

Thanks for improving Job Market Reality Check. The desktop v1.0.7 business logic and scoring engine are frozen while the public baseline stabilizes.

## Good contribution areas

- reproducible bug fixes;
- accessibility and documentation;
- tests and synthetic fixtures;
- API backward compatibility;
- privacy, packaging and installation fixes;
- read-only Skill improvements that preserve the API boundary.

New scoring dimensions, threshold changes, major UI redesigns and write-capable agent actions should begin as design discussions rather than direct pull requests.

## Development setup

Use Windows, Python 3.11+, Node.js 22+ and npm:

```powershell
python -m pip install -r .\requirements-local-api.txt

Set-Location .\extension
npm ci
npm run compile
npm run build
Set-Location ..
```

## Test with fictional data

Never add a real database, API token, browser profile, job export, resume or personal profile to a pull request.

```powershell
python .\scripts\create_ci_fixture.py `
  --output .build\ci-fixture\job_market.db

$python = (Get-Command python.exe).Source
.\run_baseline_tests.ps1 `
  -Version 1.0.7 `
  -PythonPath $python `
  -SourceDatabasePath .build\ci-fixture\job_market.db `
  -SkipPackaged `
  -SkipInstaller
```

The fixture generator refuses to overwrite an existing database and uses fictional `example.invalid` URLs.
See [the test-suite guide](tests/README.md) for categories and naming
conventions.

## Pull requests

- Keep one coherent change per pull request.
- Explain the user-visible outcome and the tests run.
- Update the API contract when a documented read response changes.
- Preserve localhost-only networking and token redaction.
- Do not claim market representativeness or offer probability.
- Confirm `git diff --check` passes.

By contributing, you agree that your changes are licensed under the MIT License.
