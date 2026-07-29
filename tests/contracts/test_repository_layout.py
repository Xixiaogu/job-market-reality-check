from __future__ import annotations

from tests.support.paths import PROJECT_ROOT


EXPECTED_DIRECTORIES = (
    "desktop",
    "docs",
    "extension",
    "local_api",
    "packaging",
    "pipeline",
    "scripts",
    "skills",
    "tests",
)

LEGACY_ROOT_FILES = (
    "analyze_boss_jobs.py",
    "audit_boss_skills.py",
    "base_science_environment.yml",
    "build_windows_desktop_shell.ps1",
    "build_windows_installer.ps1",
    "build_windows_release.ps1",
    "clean_boss_jobs.py",
    "collect_all_boss_jobs.py",
    "dashboard_management_link_v13.py",
    "dashboard_ux_v12.py",
    "desktop_app.py",
    "desktop_launcher.py",
    "extract_current_boss_job.py",
    "import_extension_jobs.py",
    "job_market_decision_system.spec",
    "job_market_desktop_shell.spec",
    "requirements-local-api.txt",
    "run_baseline_tests.ps1",
    "run_extension_pipeline.ps1",
    "run_local_api.ps1",
    "setup-phase7b2-management-ui-fixed.ps1",
    "visualize_boss_jobs_v11.py",
    "windows_glass.py",
)


def main() -> None:
    for relative_path in EXPECTED_DIRECTORIES:
        path = PROJECT_ROOT / relative_path
        assert path.is_dir(), path

    for relative_path in LEGACY_ROOT_FILES:
        path = PROJECT_ROOT / relative_path
        assert not path.exists(), path

    metadata = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'job-market-api = "local_api.cli:main"' in metadata
    assert 'job-market-desktop = "desktop.app:main"' in metadata

    assert (PROJECT_ROOT / "scripts" / "test.ps1").is_file()
    assert (PROJECT_ROOT / "scripts" / "build" / "build_desktop.ps1").is_file()
    assert (PROJECT_ROOT / "scripts" / "build" / "build_installer.ps1").is_file()
    assert (PROJECT_ROOT / "packaging" / "pyinstaller" / "desktop.spec").is_file()

    print("Repository layout contract tests passed.")


if __name__ == "__main__":
    main()
