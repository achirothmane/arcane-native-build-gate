# Localization Visual Gate — 0.1.0

Offline-first, browser-verified localization QA for development teams. Checks **actual rendered text** for clipping, viewport escape and **text/icon or control collision**. Produces a JSON evidence file, HTML report and Chromium screenshots. Fails CI on documented defects, reports `UNKNOWN` instead of false-green when a page cannot be verified.

**This is a QA and fix-verification product, not an AI auto-repair system.** It detects known classes of bugs and verifies a developer's fix. It does not claim all UI problems can be detected.

## Start

```bash
python -m pip install .
python -m playwright install chromium
lrg --config examples/online.json --output lrg-results
# Exit 0 PASS, 1 FAIL, 2 UNKNOWN (including missing targets or failed navigation)
```

Configure `base_url`, `pages`, `locales` (URL prefix, query param or cookie), `viewports`, and `critical_selectors`. Start your application locally or in CI before running. Optional `storage_state` points to a local Playwright JSON file created securely by your own login workflow; it is not collected or uploaded by the program.

### Repeatable offline smoke test

```bash
lrg --config examples/offline.json --output lrg-offline --fixture-mode
# Returns exit 1: deliberately defective fixture
```

Screenshots include page content and can contain personal data: use only dedicated test accounts and protect `lrg-results/` artifacts. Never publish customer screenshots without consent. Local reporting by default; no telemetry or API key.

## Compare a proposed fix

```bash
lrg-verify --before baseline-report/report.json --after candidate-report/report.json --output fix-verification.json
# FIX_VERIFIED_WITHIN_CHECKS (exit 0) only if earlier defects disappeared with identical check coverage
# REMAINING_DEFECTS (exit 1) if any candidate defect remains
# UNKNOWN (exit 2) on missing or mismatched coverage
```

A before/after comparison cannot rescue a false-green from a detector. Review full-size screenshots, including occlusions or interactive behavior the detector cannot measure.

## What a verdict means

- `FAIL`: clipping, viewport escape or collision detected in checked elements.
- `PASS`: none of **these checks** found a defect in configured critical regions. Not a universal guarantee.
- `UNKNOWN`: target absent, insufficient readable text, navigation failed or locale text didn't appear. Not a pass.

Read the [limitations](docs/LIMITATIONS.md) before using as a release gate.

## Current maturity

Runs locally with fixtures; workflow integration and independent application coverage require evidence. Payment checkout and independent customers are **not yet verified**. Do not describe as ready for public sales until those are checked.
