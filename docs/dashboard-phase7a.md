# Phase 7A: Dashboard UX Upgrade

This phase upgrades the generated single-file dashboard without changing the stable browser collection flow.

## Added UX

- Fixed desktop table of contents and mobile drawer.
- Reading progress bar at the top of the page.
- Six clear sections with active-section highlighting.
- Collapsible analysis sections with session persistence.
- Live SQLite job count and pipeline progress from `/api/v1/health`.
- New-result notification instead of forced refresh.
- Scroll-position restoration after refreshing a new result.
- Click-to-enlarge chart lightbox.
- Floating back-to-top control.
- Dashboard responses use `Cache-Control: no-store` to avoid stale pages.

## Pipeline integration

`pipeline/build_dashboard.py` calls `enhance_dashboard()` immediately after writing the original HTML. Future API-triggered pipeline runs therefore regenerate the enhanced dashboard automatically.

## Runtime behavior

The dashboard polls the unprotected local health endpoint every two seconds. It never receives or stores the API write token. The dashboard remains read-only.
