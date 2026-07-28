from __future__ import annotations

import hmac
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse as ManagementHTMLResponse
from fastapi.responses import HTMLResponse as ProfileHTMLResponse
from fastapi.responses import FileResponse

from . import __version__
from .config import (
    APP_MODE,
    DASHBOARD_PATH,
    DB_PATH,
    PROJECT_ROOT,
    TOKEN_PATH,
    USER_DATA_ROOT,
)
from .database import (
    count_jobs,
    get_job_record,
    initialize_database,
    latest_pipeline_run,
    recover_interrupted_pipeline_runs,
    list_job_summaries,
    upsert_extension_job,
)
from .importer_adapter import validate_payload
from .management import (
    bulk_patch_management,
    get_managed_job_record,
    get_management_history,
    initialize_management_schema,
    list_managed_jobs,
    management_counts,
    management_options,
    patch_management,
)
from .management_ui import render_management_page
from .profile import (
    create_project,
    create_skill,
    delete_project,
    delete_skill,
    direction_suggestions,
    get_full_profile,
    initialize_profile_schema,
    patch_profile,
    patch_project,
    patch_skill,
    profile_options,
    profile_onboarding_status,
    profile_summary,
    replace_locations,
    replace_preferences,
    skill_suggestions,
)
from .profile_ui import render_profile_page
from .calibration import (
    calibration_summary,
    delete_calibration_label,
    get_representative_jobs,
    initialize_calibration_schema,
    list_calibration_labels,
    upsert_calibration_label,
)
from .calibration_ui import render_calibration_page
from .decision import (
    decision_calibration_report,
    decision_options,
    decision_summary,
    get_decision,
    initialize_decision_schema,
    list_decisions,
    recalculate_decisions,
)
from .decision_ui import render_decision_page
from .desktop_runtime import (
    complete_setup,
    desktop_status,
    open_extension_folder,
    open_user_data_folder,
    record_extension_activity,
)
from .pipeline import schedule_pipeline
from .security import get_or_create_token
from .setup_ui import render_launch_page, render_setup_page


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    initialize_management_schema()
    initialize_profile_schema()
    initialize_calibration_schema()
    initialize_decision_schema()
    recover_interrupted_pipeline_runs()
    get_or_create_token()
    yield


app = FastAPI(
    title="Job Market Reality Check Local API",
    version=__version__,
    description=(
        "本地岗位采集、SQLite 存储和 Python 分析管线接口。"
        "服务仅监听 127.0.0.1。"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Job-Market-Token"],
)


def require_token(
    x_job_market_token: Annotated[
        str | None,
        Header(),
    ] = None,
) -> None:
    expected = get_or_create_token()
    provided = x_job_market_token or ""

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或错误的 X-Job-Market-Token。",
        )


Protected = Annotated[None, Depends(require_token)]


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "job-market-reality-check-local-api",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
        "dashboard": "/dashboard",
        "manage": "/manage",
        "profile": "/profile",
        "calibrate": "/calibrate",
        "decision": "/decision",
        "setup": "/setup",
        "decision_api": "/api/v1/decision/summary",
    }


# PHASE_91_DESKTOP_PRODUCTIZATION
@app.get(
    "/launch",
    response_class=ManagementHTMLResponse,
)
def launch_page(
    next_path: str = Query(default="/decision", alias="next"),
) -> ManagementHTMLResponse:
    return ManagementHTMLResponse(
        content=render_launch_page(next_path),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get(
    "/setup",
    response_class=ManagementHTMLResponse,
)
def setup_page() -> ManagementHTMLResponse:
    return ManagementHTMLResponse(
        content=render_setup_page(),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/dashboard")
def dashboard() -> FileResponse:
    if not DASHBOARD_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板尚未生成。",
        )

    return FileResponse(
        DASHBOARD_PATH,
        media_type="text/html; charset=utf-8",
        filename="job_market_dashboard_v12.html",
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get(
    "/manage",
    response_class=ManagementHTMLResponse,
)
def management_page() -> ManagementHTMLResponse:
    return ManagementHTMLResponse(
        content=render_management_page(),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get(
    "/profile",
    response_class=ProfileHTMLResponse,
)
def profile_page() -> ProfileHTMLResponse:
    return ProfileHTMLResponse(
        content=render_profile_page(),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get(
    "/calibrate",
    response_class=ManagementHTMLResponse,
)
def calibration_page() -> ManagementHTMLResponse:
    return ManagementHTMLResponse(
        content=render_calibration_page(),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/v1/desktop/status")
def read_desktop_status(_: Protected) -> dict[str, Any]:
    return desktop_status(job_count=count_jobs())


@app.post("/api/v1/desktop/complete-setup")
def finish_desktop_setup(_: Protected) -> dict[str, Any]:
    state = complete_setup()
    return {"ok": True, "setup_completed": bool(state.get("setup_completed"))}


@app.post("/api/v1/desktop/open-extension-folder")
def show_extension_folder(_: Protected) -> dict[str, Any]:
    try:
        return open_extension_folder()
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@app.post("/api/v1/desktop/open-user-data-folder")
def show_user_data_folder(_: Protected) -> dict[str, Any]:
    try:
        return open_user_data_folder()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# PHASE_82C_DECISION_CENTER_API
@app.get(
    "/decision",
    response_class=ManagementHTMLResponse,
)
def decision_page() -> ManagementHTMLResponse:
    return ManagementHTMLResponse(
        content=render_decision_page(),
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    latest_run = latest_pipeline_run()
    return {
        "ok": True,
        "service": "job-market-reality-check-local-api",
        "version": __version__,
        "app_mode": APP_MODE,
        "project_root": str(PROJECT_ROOT),
        "user_data_root": str(USER_DATA_ROOT),
        "database_path": str(DB_PATH),
        "job_count": count_jobs(),
        "dashboard_exists": DASHBOARD_PATH.exists(),
        "dashboard_path": str(DASHBOARD_PATH),
        "dashboard_url": "/dashboard",
        "latest_pipeline": latest_run,
        "management": management_counts(),
        "profile": profile_summary(),
    }


@app.get("/api/v1/jobs")
def jobs(
    _: Protected,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    user_status: str | None = Query(default=None),
    listing_status: str | None = Query(default=None),
    quality_override: str | None = Query(default=None),
    archived: bool | None = Query(default=None),
    category_manual: str | None = Query(default=None),
    city: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
) -> dict[str, Any]:
    try:
        return list_managed_jobs(
            limit=limit,
            offset=offset,
            user_status=user_status,
            listing_status=listing_status,
            quality_override=quality_override,
            archived=archived,
            category_manual=category_manual,
            city=city,
            keyword=keyword,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/jobs/{job_id}")
def job_detail(
    job_id: str,
    _: Protected,
) -> dict[str, Any]:
    record = get_managed_job_record(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在。",
        )
    return record


@app.get("/api/v1/jobs/{job_id}/history")
def job_management_history(
    job_id: str,
    _: Protected,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    try:
        items = get_management_history(job_id, limit=limit)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job_id,
        "total": len(items),
        "items": items,
    }


@app.patch("/api/v1/jobs/{job_id}/management")
def update_job_management(
    job_id: str,
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
    run_pipeline: bool = False,
) -> dict[str, Any]:
    try:
        result = patch_management(job_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    response: dict[str, Any] = {
        "ok": True,
        **result,
    }

    if (
        run_pipeline
        and result["analysis_required"]
        and result["changed"]
    ):
        response["pipeline"] = schedule_pipeline()

    return response


@app.post("/api/v1/jobs/bulk-management")
def update_jobs_management_bulk(
    _: Protected,
    body: Annotated[dict[str, Any], Body()],
    run_pipeline: bool = False,
) -> dict[str, Any]:
    job_ids = body.get("job_ids")
    patch = body.get("patch")

    if not isinstance(job_ids, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job_ids 必须是数组。",
        )

    if not isinstance(patch, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="patch 必须是 JSON 对象。",
        )

    try:
        result = bulk_patch_management(job_ids, patch)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    response: dict[str, Any] = {
        "ok": result["failed"] == 0,
        **result,
    }

    if (
        run_pipeline
        and result["analysis_required"]
        and result["changed"] > 0
    ):
        response["pipeline"] = schedule_pipeline()

    return response


@app.get("/api/v1/management/options")
def get_management_options(
    _: Protected,
) -> dict[str, Any]:
    return management_options()


@app.get("/api/v1/management/summary")
def get_management_summary(
    _: Protected,
) -> dict[str, Any]:
    return management_counts()


@app.get("/api/v1/profile")
def read_profile(_: Protected) -> dict[str, Any]:
    return get_full_profile()


@app.patch("/api/v1/profile")
def update_profile(
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        return {"ok": True, **patch_profile(payload)}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/profile/onboarding")
def get_profile_onboarding(_: Protected) -> dict[str, Any]:
    return profile_onboarding_status()


@app.get("/api/v1/profile/options")
def get_profile_options(_: Protected) -> dict[str, Any]:
    return profile_options()


@app.put("/api/v1/profile/cities")
def update_profile_cities(
    _: Protected,
    body: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        items = replace_locations(body.get("cities", []))
        return {"ok": True, "cities": items}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/profile/skills")
def read_profile_skills(_: Protected) -> dict[str, Any]:
    return {"items": get_full_profile()["skills"]}


@app.post("/api/v1/profile/skills")
def add_profile_skill(
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        return {"ok": True, "skill": create_skill(payload)}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.patch("/api/v1/profile/skills/{skill_id}")
def update_profile_skill(
    skill_id: int,
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        return {"ok": True, "skill": patch_skill(skill_id, payload)}
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.delete("/api/v1/profile/skills/{skill_id}")
def remove_profile_skill(
    skill_id: int,
    _: Protected,
) -> dict[str, Any]:
    try:
        return {"ok": True, **delete_skill(skill_id)}
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/profile/skill-suggestions")
def get_skill_suggestions(
    _: Protected,
    query: str | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    return skill_suggestions(query=query, limit=limit)


@app.get("/api/v1/profile/projects")
def read_profile_projects(_: Protected) -> dict[str, Any]:
    return {"items": get_full_profile()["projects"]}


@app.post("/api/v1/profile/projects")
def add_profile_project(
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        return {"ok": True, "project": create_project(payload)}
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.patch("/api/v1/profile/projects/{project_id}")
def update_profile_project(
    project_id: int,
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        return {"ok": True, "project": patch_project(project_id, payload)}
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.delete("/api/v1/profile/projects/{project_id}")
def remove_profile_project(
    project_id: int,
    _: Protected,
) -> dict[str, Any]:
    try:
        return {"ok": True, **delete_project(project_id)}
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@app.put("/api/v1/profile/preferences")
def update_profile_preferences(
    _: Protected,
    body: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        items = replace_preferences(body.get("directions", []))
        return {"ok": True, "directions": items}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/profile/direction-suggestions")
def get_direction_suggestions(
    _: Protected,
    query: str | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    return direction_suggestions(query=query, limit=limit)


@app.get("/api/v1/calibration/representatives")
def read_calibration_representatives(
    _: Protected,
    limit: Annotated[int, Query(ge=1, le=10)] = 10,
) -> dict[str, Any]:
    return get_representative_jobs(limit=limit)


@app.post("/api/v1/calibration/representatives/refresh")
def refresh_calibration_representatives(
    _: Protected,
    limit: Annotated[int, Query(ge=1, le=10)] = 10,
) -> dict[str, Any]:
    return get_representative_jobs(limit=limit, refresh=True)


@app.get("/api/v1/calibration/labels")
def read_calibration_labels(_: Protected) -> dict[str, Any]:
    items = list_calibration_labels()
    return {"total": len(items), "items": items}


@app.put("/api/v1/calibration/labels/{job_id}")
def save_calibration_label(
    job_id: str,
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    try:
        label = upsert_calibration_label(job_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return {"ok": True, "label": label}


@app.delete("/api/v1/calibration/labels/{job_id}")
def remove_calibration_label(
    job_id: str,
    _: Protected,
) -> dict[str, Any]:
    return {"ok": True, **delete_calibration_label(job_id)}


@app.get("/api/v1/calibration/summary")
def read_calibration_summary(_: Protected) -> dict[str, Any]:
    return calibration_summary()




# PHASE_82B_EXPLAINABLE_DECISION_API
@app.get("/api/v1/decision/options")
def get_decision_options(_: Protected) -> dict[str, Any]:
    return decision_options()


# DECISION_REFRESH_V1
@app.post("/api/v1/decision/recalculate")
def recalculate_decision_scores(
    _: Protected,
    strategy: str = Query(default="balanced"),
    pending_only: bool = Query(default=True),
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> dict[str, Any]:
    try:
        result = recalculate_decisions(strategy=strategy)
        return {
            **result,
            "summary": decision_summary(strategy=strategy),
            "jobs": list_decisions(
                strategy=strategy,
                pending_only=pending_only,
                limit=limit,
            ),
            "calibration": decision_calibration_report(strategy=strategy),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/decision/summary")
def read_decision_summary(
    _: Protected,
    strategy: str = Query(default="balanced"),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return decision_summary(strategy=strategy, refresh=refresh)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/decision/jobs")
def read_decision_jobs(
    _: Protected,
    strategy: str = Query(default="balanced"),
    action_group: str | None = Query(default=None),
    pending_only: bool = Query(default=True),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return list_decisions(
            strategy=strategy,
            action_group=action_group,
            pending_only=pending_only,
            limit=limit,
            offset=offset,
            refresh=refresh,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/decision/jobs/{job_id}")
def read_decision_job(
    job_id: str,
    _: Protected,
    strategy: str = Query(default="balanced"),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return get_decision(job_id, strategy=strategy, refresh=refresh)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/decision/calibration")
def read_decision_calibration(
    _: Protected,
    strategy: str = Query(default="balanced"),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return decision_calibration_report(strategy=strategy, refresh=refresh)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.post("/api/v1/jobs/upsert")
def upsert_job(
    _: Protected,
    payload: Annotated[dict[str, Any], Body()],
    run_pipeline: bool = False,
) -> dict[str, Any]:
    issues = validate_payload(payload)
    if issues:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=issues,
        )

    result = upsert_extension_job(payload)
    record_extension_activity(
        source="single_upsert",
        imported_count=1,
    )
    response: dict[str, Any] = {
        "ok": True,
        "action": result["action"],
        "job_id": result["job_id"],
        "revision": result["revision"],
        "job_count": count_jobs(),
    }

    if run_pipeline:
        response["pipeline"] = schedule_pipeline()

    return response


@app.post("/api/v1/jobs/bulk-upsert")
def bulk_upsert_jobs(
    _: Protected,
    body: Annotated[Any, Body()],
    run_pipeline: bool = False,
) -> dict[str, Any]:
    if isinstance(body, list):
        payloads = body
    elif isinstance(body, dict) and isinstance(body.get("jobs"), list):
        payloads = body["jobs"]
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请求体必须是岗位数组，或包含 jobs 数组的对象。",
        )

    results = {
        "input": len(payloads),
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "failed": 0,
        "errors": [],
    }

    for index, payload in enumerate(payloads, start=1):
        if not isinstance(payload, dict):
            results["failed"] += 1
            results["errors"].append(
                f"第{index}条不是 JSON 对象。"
            )
            continue

        issues = validate_payload(payload)
        if issues:
            results["failed"] += 1
            results["errors"].append(
                {
                    "index": index,
                    "issues": issues,
                }
            )
            continue

        result = upsert_extension_job(payload)
        results[result["action"]] += 1

    successful_count = len(payloads) - results["failed"]
    if successful_count > 0:
        record_extension_activity(
            source="bulk_upsert",
            imported_count=successful_count,
        )

    response: dict[str, Any] = {
        "ok": results["failed"] == 0,
        "results": results,
        "job_count": count_jobs(),
    }

    if run_pipeline and results["failed"] == 0:
        response["pipeline"] = schedule_pipeline()

    return response


@app.post("/api/v1/pipeline/run")
def run_pipeline(_: Protected) -> dict[str, Any]:
    result = schedule_pipeline()
    return {
        "ok": True,
        **result,
    }


@app.get("/api/v1/pipeline/status")
def pipeline_status(_: Protected) -> dict[str, Any]:
    return {
        "run": latest_pipeline_run(),
        "dashboard_exists": DASHBOARD_PATH.exists(),
        "dashboard_path": str(DASHBOARD_PATH),
    }


@app.get("/api/v1/runtime")
def runtime_info(_: Protected) -> dict[str, str]:
    return {
        "app_mode": APP_MODE,
        "user_data_root": str(USER_DATA_ROOT),
        "database_path": str(DB_PATH),
        "token_path": str(TOKEN_PATH),
        "dashboard_path": str(DASHBOARD_PATH),
    }


# PHASE_7B1_MANAGEMENT


# PHASE_7B2_MANAGEMENT_UI


# PHASE_81_PROFILE_API


# PHASE_81C_COLD_START_API


# PHASE_82A_CALIBRATION_API

# UNIFIED_APP_SHELL_V1_INSTALL
from .app_shell import install_unified_app_shell

install_unified_app_shell(app)
