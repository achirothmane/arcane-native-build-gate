# Full running Arcane test — issue #3899

This is a **real Docker + Chromium experiment**, NOT a mock DOM. Builds upstream Arcane v2.10.2 into baseline and candidate Docker images, starts the Go backend, authenticates a fresh test admin, selects French and measures whether real navigation labels are clipped. Screenshots, browser geometry, Docker logs and reproducible patch are uploaded to Actions artifacts.

[Runtime Workflow](../.github/workflows/arcane-full-runtime.yml).

**Strict interpretation:**
- RUNTIME_FIX_SUPPORTED requires the original UI to exhibit clipping and the patched UI not to, with a real logged-in French UI.
- BASELINE_BUG_NOT_REPRODUCED means **no fix proved**; the UI may be different from the reporter's settings.
- UNKNOWN / failed test is **not** evidence of a fix.
- The test covers v2.10.2 and one reported defect #3899 only. It does not automatically validate other versions or other defects. No AI is used; changes are deterministic.

Only disposable test passwords and data. No changes to upstream or production repos.
