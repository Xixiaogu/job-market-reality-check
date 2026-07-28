from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="job-market-skill-") as directory:
        output = Path(directory)
        completed = subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_job_market.py"),
                "--jobs", str(root / "examples" / "sample_jobs.json"),
                "--profile", str(root / "examples" / "sample_profile.json"),
                "--labels", str(root / "examples" / "sample_labels.json"),
                "--output-dir", str(output),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert completed.returncode == 0, completed.stdout
        results = json.loads((output / "decision_results.json").read_text(encoding="utf-8"))
        report = (output / "report.md").read_text(encoding="utf-8")
        assert results["summary"]["usable_jobs"] == 4
        assert len(results["jobs"]) == 4
        assert results["calibration"]["count"] == 4
        assert all(0 <= item["priority"] <= 100 for item in results["jobs"])
        assert "求职市场现实检查" in report
        assert "Offer概率" in report
        assert "api_token" not in report.lower()
    print("Job Market Reality Check Skill tests passed.")


if __name__ == "__main__":
    main()
