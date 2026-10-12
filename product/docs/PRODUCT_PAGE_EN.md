# Localization Visual Gate — Team Edition

**Find multilingual UI breakage before release. No monitoring SaaS needed.**

When translations get longer, web apps can ship clipped labels and overlapping controls. Localization Visual Gate runs in Chromium against your actual staging app and issues a reviewable QA report for selected pages, languages and viewport sizes.

## Included

- Locale matrices using URL paths, query parameters or cookies.
- Real-browser checks for known clipping patterns, off-viewport text and overlapping buttons/icons.
- Before/after fix verification which refuses false-green when coverage changes.
- HTML + JSON reports and Chromium screenshot evidence.
- CI-friendly exit status: 0 PASS, 1 FAIL, 2 UNKNOWN.
- Local-only operation: no hosted account or telemetry.

**Delivery:** a ZIP with installable Python wheel, inspectable source, sample configurations, browser QA tests and usage instructions. Requirements: Python 3.10+ and Playwright Chromium.

**Introductory price hypothesis: $39 USD one-time for one internal team.** Not validated by paying customers.

**Not promised:** AI-driven general-purpose repair, browser-perfect visuals, Safari compatibility, all authentication systems, or revenue guarantees. The configured critical regions must be reviewed alongside screenshots.

**Payment:** The live product checkout is not yet active. Do not treat a storefront homepage as a product-specific checkout.
