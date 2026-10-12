# Verification boundaries

The scanner checks configured regions, not the whole app automatically. It can miss text occluded by backgrounds, images, pseudo-elements, font fallback, non-English line breaks, focus order/accessibility problems, hidden translations, runtime changes not captured after settle, or defects that require user interaction. Coverage depends on the locale routing and page selectors configured by the buyer. Reflow on scroll and browser differences (Safari / Firefox) are not covered in version 0.1.

`PASS` should be read as **no detected known defect among evaluated regions**, not a guarantee of visual correctness. `UNKNOWN` cannot be treated as passing a CI gate. `--fixture-mode` is only for offline demonstration, not proof against a deployed site.

No automatic repair of arbitrary CSS/JS. Source code stays local; `storage_state` credentials are loaded locally without intentional upload. Screenshots and reports may contain end-user content; restrict their access.
