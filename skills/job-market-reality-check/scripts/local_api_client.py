from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


CONTRACT_VERSION = "1.0.0"
DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_STRATEGY = "balanced"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class LocalAPIError(RuntimeError):
    """Base error for local API failures."""


class LocalAPIConnectionError(LocalAPIError):
    """The local service could not be reached."""


class LocalAPIAuthError(LocalAPIError):
    """The local API token is missing or rejected."""


class LocalAPIResponseError(LocalAPIError):
    """The local service returned a non-success response."""


class LocalAPIContractError(LocalAPIError):
    """The response does not satisfy the frozen Skill v1 contract."""


def _require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LocalAPIContractError(f"{context} must be a JSON object.")
    return value


def _require_keys(
    payload: dict[str, Any],
    keys: tuple[str, ...],
    context: str,
) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise LocalAPIContractError(
            f"{context} is missing required fields: {', '.join(missing)}"
        )


def _run_id(payload: dict[str, Any], context: str) -> int:
    run = _require_object(payload.get("run"), f"{context}.run")
    if "run_id" not in run:
        raise LocalAPIContractError(f"{context}.run is missing run_id.")
    try:
        return int(run["run_id"])
    except (TypeError, ValueError) as exc:
        raise LocalAPIContractError(
            f"{context}.run.run_id must be an integer."
        ) from exc


def default_token_candidates() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("JOB_MARKET_API_TOKEN_PATH")
    if explicit:
        candidates.append(Path(explicit))

    user_data = os.environ.get("JOB_MARKET_USER_DATA_DIR")
    if user_data:
        candidates.append(Path(user_data) / "runtime" / "api_token.txt")

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(
            Path(local_app_data)
            / "JobMarketDecisionSystem"
            / "runtime"
            / "api_token.txt"
        )

    repository_root = Path(__file__).resolve().parents[3]
    candidates.append(repository_root / "local_api" / "runtime" / "api_token.txt")
    return list(dict.fromkeys(path.resolve() for path in candidates))


def read_local_token(path: Path | None = None) -> str:
    candidates = [path.resolve()] if path else default_token_candidates()
    for candidate in candidates:
        try:
            token = candidate.read_text(encoding="utf-8-sig").strip()
        except OSError:
            continue
        if len(token) >= 32:
            return token
    raise LocalAPIAuthError(
        "Local API token was not found. Start the desktop app or provide "
        "--token-file. The token value must never be pasted into chat."
    )


class LocalAPIClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        token: str | None = None,
        token_path: Path | None = None,
        timeout: float = 10.0,
    ) -> None:
        parsed = urllib.parse.urlparse(base_url.rstrip("/"))
        if parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS:
            raise ValueError(
                "The Skill v1 client only sends credentials to a local HTTP host."
            )
        if timeout <= 0:
            raise ValueError("timeout must be positive.")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._token_path = token_path
        self.timeout = float(timeout)

    def _protected_token(self) -> str:
        if self._token is None:
            self._token = read_local_token(self._token_path)
        if len(self._token) < 32:
            raise LocalAPIAuthError("The local API token is invalid.")
        return self._token

    def _get(
        self,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        protected: bool = True,
    ) -> dict[str, Any]:
        if not path.startswith("/api/v1/"):
            raise ValueError("Only frozen /api/v1 read endpoints are allowed.")
        encoded_query = urllib.parse.urlencode(
            {
                key: str(value).lower() if isinstance(value, bool) else value
                for key, value in (query or {}).items()
                if value is not None
            }
        )
        url = self.base_url + path
        if encoded_query:
            url += "?" + encoded_query
        headers = {
            "Accept": "application/json",
            "User-Agent": "job-market-reality-check-skill/0.1",
        }
        if protected:
            headers["X-Job-Market-Token"] = self._protected_token()
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise LocalAPIAuthError(
                    "Local API authentication failed. Re-pair the desktop app."
                ) from exc
            if exc.code == 404:
                raise LocalAPIResponseError(
                    "The requested local record does not exist (HTTP 404)."
                ) from exc
            if exc.code == 422:
                raise LocalAPIResponseError(
                    "The local API rejected an incompatible parameter (HTTP 422)."
                ) from exc
            raise LocalAPIResponseError(
                f"The local API returned HTTP {exc.code}."
            ) from exc
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise LocalAPIConnectionError(
                "Could not connect to the local API. Start the desktop app and retry."
            ) from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalAPIContractError(
                "The local API did not return valid UTF-8 JSON."
            ) from exc
        return _require_object(payload, path)

    def health(self) -> dict[str, Any]:
        payload = self._get("/api/v1/health", protected=False)
        _require_keys(
            payload,
            ("ok", "service", "version", "app_mode", "job_count"),
            "health",
        )
        if payload["ok"] is not True:
            raise LocalAPIContractError("The local API health check is not OK.")
        return payload

    def management_summary(self) -> dict[str, Any]:
        payload = self._get("/api/v1/management/summary")
        _require_keys(
            payload,
            ("total", "active", "archived", "by_user_status"),
            "management summary",
        )
        return payload

    def profile(self) -> dict[str, Any]:
        payload = self._get("/api/v1/profile")
        _require_keys(
            payload,
            (
                "profile",
                "cities",
                "skills",
                "projects",
                "directions",
                "summary",
                "onboarding",
            ),
            "profile",
        )
        return payload

    def decision_options(self) -> dict[str, Any]:
        payload = self._get("/api/v1/decision/options")
        _require_keys(
            payload,
            ("engine_version", "default_strategy", "strategies"),
            "decision options",
        )
        return payload

    def decision_summary(
        self,
        *,
        strategy: str = DEFAULT_STRATEGY,
    ) -> dict[str, Any]:
        payload = self._get(
            "/api/v1/decision/summary",
            query={"strategy": strategy},
        )
        _require_keys(
            payload,
            (
                "run",
                "strategy",
                "job_count",
                "queue_count",
                "by_action_group",
                "top_jobs",
            ),
            "decision summary",
        )
        _run_id(payload, "decision summary")
        return payload

    def jobs(
        self,
        *,
        archived: bool = False,
        keyword: str | None = None,
        city: str | None = None,
    ) -> dict[str, Any]:
        return self._paginate(
            lambda limit, offset: self._get(
                "/api/v1/jobs",
                query={
                    "limit": limit,
                    "offset": offset,
                    "archived": archived,
                    "keyword": keyword,
                    "city": city,
                },
            ),
            context="jobs",
        )

    def job(self, job_id: str) -> dict[str, Any]:
        encoded = urllib.parse.quote(str(job_id), safe="")
        payload = self._get(f"/api/v1/jobs/{encoded}")
        _require_keys(payload, ("job_id", "canonical", "management"), "job")
        return payload

    def job_history(
        self,
        job_id: str,
        *,
        limit: int = 100,
    ) -> dict[str, Any]:
        encoded = urllib.parse.quote(str(job_id), safe="")
        payload = self._get(
            f"/api/v1/jobs/{encoded}/history",
            query={"limit": max(1, min(int(limit), 500))},
        )
        _require_keys(payload, ("job_id", "total", "items"), "job history")
        return payload

    def decision_jobs(
        self,
        *,
        strategy: str = DEFAULT_STRATEGY,
        action_group: str | None = None,
        pending_only: bool = True,
    ) -> dict[str, Any]:
        expected_run_id: int | None = None

        def fetch(limit: int, offset: int) -> dict[str, Any]:
            nonlocal expected_run_id
            payload = self._get(
                "/api/v1/decision/jobs",
                query={
                    "strategy": strategy,
                    "action_group": action_group,
                    "pending_only": pending_only,
                    "limit": limit,
                    "offset": offset,
                },
            )
            current_run_id = _run_id(payload, "decision jobs")
            if expected_run_id is None:
                expected_run_id = current_run_id
            elif current_run_id != expected_run_id:
                raise LocalAPIContractError(
                    "Decision run changed while reading paginated results."
                )
            return payload

        result = self._paginate(fetch, context="decision jobs")
        result["run_id"] = expected_run_id
        return result

    def decision_job(
        self,
        job_id: str,
        *,
        strategy: str = DEFAULT_STRATEGY,
    ) -> dict[str, Any]:
        encoded = urllib.parse.quote(str(job_id), safe="")
        payload = self._get(
            f"/api/v1/decision/jobs/{encoded}",
            query={"strategy": strategy},
        )
        _require_keys(payload, ("run", "item"), "decision job")
        _run_id(payload, "decision job")
        return payload

    def decision_calibration(
        self,
        *,
        strategy: str = DEFAULT_STRATEGY,
    ) -> dict[str, Any]:
        payload = self._get(
            "/api/v1/decision/calibration",
            query={"strategy": strategy},
        )
        _require_keys(
            payload,
            ("run", "strategy", "label_count", "hard_conflict_misses"),
            "decision calibration",
        )
        _run_id(payload, "decision calibration")
        return payload

    def brief_context(
        self,
        *,
        strategy: str = DEFAULT_STRATEGY,
    ) -> dict[str, Any]:
        health = self.health()
        options = self.decision_options()
        management = self.management_summary()
        profile = self.profile()
        summary = self.decision_summary(strategy=strategy)
        decisions = self.decision_jobs(
            strategy=strategy,
            pending_only=True,
        )
        summary_run_id = _run_id(summary, "decision summary")
        if decisions["run_id"] != summary_run_id:
            raise LocalAPIContractError(
                "Decision summary and queue use different decision runs."
            )
        return {
            "contract_version": CONTRACT_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "service_version": health["version"],
                "engine_version": options["engine_version"],
                "decision_run_id": summary_run_id,
                "decision_created_at": summary["run"].get("created_at"),
                "strategy": strategy,
            },
            "health": {
                "ok": health["ok"],
                "service": health["service"],
                "version": health["version"],
                "app_mode": health["app_mode"],
                "job_count": health["job_count"],
            },
            "management": management,
            "profile": profile,
            "decision_summary": summary,
            "decision_jobs": decisions["items"],
        }

    @staticmethod
    def _paginate(
        fetch_page: Callable[[int, int], dict[str, Any]],
        *,
        context: str,
    ) -> dict[str, Any]:
        limit = 500
        offset = 0
        items: list[dict[str, Any]] = []
        expected_total: int | None = None
        first_payload: dict[str, Any] | None = None
        while expected_total is None or len(items) < expected_total:
            payload = fetch_page(limit, offset)
            _require_keys(payload, ("total", "items"), context)
            page_items = payload["items"]
            if not isinstance(page_items, list):
                raise LocalAPIContractError(f"{context}.items must be an array.")
            try:
                total = int(payload["total"])
            except (TypeError, ValueError) as exc:
                raise LocalAPIContractError(
                    f"{context}.total must be an integer."
                ) from exc
            if expected_total is None:
                expected_total = total
                first_payload = payload
            elif total != expected_total:
                raise LocalAPIContractError(
                    f"{context}.total changed while reading pages."
                )
            items.extend(
                _require_object(item, f"{context}.items[]")
                for item in page_items
            )
            if not page_items:
                break
            offset += len(page_items)
        if expected_total is None or first_payload is None:
            raise LocalAPIContractError(f"{context} returned no page.")
        if len(items) != expected_total:
            raise LocalAPIContractError(
                f"{context} returned {len(items)} items but declared {expected_total}."
            )
        return {
            "total": expected_total,
            "items": items,
            "first_page": first_payload,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only client for the local Job Market desktop API."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("JOB_MARKET_API_URL", DEFAULT_BASE_URL),
    )
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--timeout", type=float, default=10.0)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health")
    brief = subparsers.add_parser("brief")
    brief.add_argument("--strategy", default=DEFAULT_STRATEGY)
    brief.add_argument("--output", type=Path)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        client = LocalAPIClient(
            base_url=args.base_url,
            token_path=args.token_file,
            timeout=args.timeout,
        )
        if args.command == "health":
            health = client.health()
            payload = {
                key: health[key]
                for key in ("ok", "service", "version", "app_mode", "job_count")
            }
        else:
            payload = client.brief_context(strategy=args.strategy)
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        if getattr(args, "output", None):
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
            print(f"Brief context written to: {args.output}")
        else:
            print(rendered)
        return 0
    except (LocalAPIError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
