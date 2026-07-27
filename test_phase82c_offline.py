from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from local_api.decision_ui import PAGE_VERSION, render_decision_page
from local_api.main import app


def main() -> None:
    html = render_decision_page()
    assert PAGE_VERSION == "8.2C"
    assert "PHASE_82C_DECISION_CENTER_UI" not in html
    assert "投递决策中心" in html
    assert "/api/v1/decision/summary" in html
    assert "/api/v1/decision/jobs" in html
    assert "/api/v1/decision/calibration" in html
    assert "/api/v1/jobs/" in html
    assert "jobMarketApiTokenV1" in html
    assert "只看待投递队列" in html
    assert "标记已投递" in html
    assert "立即投递" in html
    assert "值得冲刺" in html
    assert "补材料后投递" in html
    assert "暂缓" in html

    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/decision" in route_paths
    assert "/api/v1/decision/summary" in route_paths
    assert "/api/v1/jobs/{job_id}/management" in route_paths

    match = re.search(r"<script>(.*?)</script>", html, flags=re.S)
    assert match is not None
    javascript = match.group(1)
    assert "openDetail" in javascript
    assert "saveStatus" in javascript
    assert "pending_only=" in javascript

    node = shutil.which("node")
    if node:
        with tempfile.TemporaryDirectory(prefix="job-market-phase82c-js-") as directory:
            script_path = Path(directory) / "decision-ui.js"
            script_path.write_text(javascript, encoding="utf-8")
            result = subprocess.run(
                [node, "--check", str(script_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            assert result.returncode == 0, result.stderr

    print("Phase 8.2C decision center offline test passed.")


if __name__ == "__main__":
    main()
