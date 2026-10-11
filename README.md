# Arcane Native Build Gate

Independent read-only native build experiment, **not a released localization repair product**.

## Verified result — October 11, 2026

**3 of 3 pinned Arcane versions passed original baseline and candidate Svelte check and native build.**

- v2.10.2 — baseline check/build PASS; candidate check/build PASS.
- v2.12.0 — baseline check/build PASS; candidate check/build PASS.
- v2.14.0 — baseline check/build PASS; candidate check/build PASS.

**Runtime visual repair remains UNKNOWN.** Building successfully does not demonstrate that the bug is fixed in a running Arcane application. No commercial validation exists.

[Arabic evidence report](RUN_RESULT_AR.md) | [Successful GitHub Actions run](https://github.com/achirothmane/arcane-native-build-gate/actions/runs/38179315515) | [Workflow source](.github/workflows/arcane-native-build-gate.yml) | [Arabic usage guidance](README_AR.md)

CI builds exact pinned public Arcane revisions on GitHub-hosted runners with read-only GitHub permissions, compiles Paraglide translation code, checks the baseline, verifies Git blob hashes before modifications, builds the candidate and uploads logs and diff artifacts. No commit or PR is sent upstream.

**Decision: TEST ONLY / NO RELEASE.**
