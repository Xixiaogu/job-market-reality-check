from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
SPEC = importlib.util.spec_from_file_location(
    "job_market_local_api_client",
    ROOT / "scripts" / "local_api_client.py",
)
assert SPEC and SPEC.loader
CLIENT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT_MODULE)


def main() -> None:
    token_path = REPOSITORY_ROOT / "local_api" / "runtime" / "api_token.txt"
    client = CLIENT_MODULE.LocalAPIClient(
        base_url=os.environ.get(
            "JOB_MARKET_API_URL",
            "http://127.0.0.1:8765",
        ),
        token_path=token_path,
    )
    context = client.brief_context()
    assert context["contract_version"] == "1.0.0"
    assert context["metadata"]["strategy"] == "balanced"
    assert isinstance(context["metadata"]["decision_run_id"], int)
    assert context["health"]["ok"] is True
    assert context["decision_summary"]["queue_count"] == len(
        context["decision_jobs"]
    )
    assert context["decision_summary"]["run"]["run_id"] == context[
        "metadata"
    ]["decision_run_id"]
    serialized = json.dumps(context, ensure_ascii=False).lower()
    assert "api_token" not in serialized
    assert "database_path" not in serialized
    assert "project_root" not in serialized
    assert "user_data_root" not in serialized
    print("Skill local API integration test passed.")


if __name__ == "__main__":
    main()
