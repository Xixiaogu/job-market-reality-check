from __future__ import annotations

import re
from pathlib import Path
from typing import Any

START_MARKER = "<!-- JOB_MANAGEMENT_LINK_START -->"
END_MARKER = "<!-- JOB_MANAGEMENT_LINK_END -->"

BLOCK = r'''
<!-- JOB_MANAGEMENT_LINK_START -->
<style>
#job-management-link{position:fixed;z-index:9200;right:22px;top:22px;display:inline-flex;align-items:center;min-height:40px;border:1px solid #9dd1cb;border-radius:12px;padding:8px 14px;color:#075e57;background:rgba(255,255,255,.96);box-shadow:0 8px 24px rgba(18,55,62,.12);backdrop-filter:blur(12px);text-decoration:none;font-family:Inter,"PingFang SC","Microsoft YaHei",system-ui,sans-serif;font-size:12px;font-weight:780}
#job-management-link:hover{background:#effaf8}@media(max-width:760px){#job-management-link{top:auto;right:16px;bottom:74px}}
</style>
<a id="job-management-link" href="/manage" target="_blank" rel="noreferrer">岗位管理中心</a>
<script>(()=>{const a=document.getElementById('job-management-link');if(a)a.href=location.protocol==='file:'?'http://127.0.0.1:8765/manage':'/manage'})();</script>
<!-- JOB_MANAGEMENT_LINK_END -->
'''


def enhance_management_link(path: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dashboard not found: {path}")

    html = path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    html = pattern.sub("", html)

    if "</body>" not in html:
        raise ValueError("Dashboard HTML is missing </body>.")

    html = html.replace("</body>", BLOCK + "\n</body>", 1)
    path.write_text(html, encoding="utf-8")

    return {
        "dashboard_path": str(path),
        "size_bytes": path.stat().st_size,
    }
