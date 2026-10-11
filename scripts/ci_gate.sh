#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:?Version required}"
mkdir -p evidence
cd arcane
export CI=true
pnpm install --frozen-lockfile 2>&1 | tee ../evidence/pnpm-install.log
pnpm --filter arcane-frontend paraglide:compile 2>&1 | tee ../evidence/paraglide-compile.log

function gate() {
  local label="$1"
  set +e
  pnpm --filter arcane-frontend check >"../evidence/${label}-check.log" 2>&1
  local checked=$?
  pnpm --filter arcane-frontend build >"../evidence/${label}-build.log" 2>&1
  local built=$?
  set -e
  printf 'check=%s\nbuild=%s\n' "$checked" "$built" >"../evidence/${label}-status.txt"
  printf '%s: check=%s build=%s\n' "$label" "$checked" "$built"
  [[ "$checked" == 0 && "$built" == 0 ]]
}
if ! gate baseline; then
  echo 'BASELINE_FAILED: cannot attribute later failure to candidate' | tee ../evidence/verdict.txt
  exit 3
fi
python3 ../scripts/apply_candidates.py --root . --version "$VERSION" --manifest ../evidence/patch-manifest.json
git diff --check 2>&1 | tee ../evidence/diff-check.log
git diff -- frontend/src/ > ../evidence/patch-against-original.diff
if ! gate candidate; then
  echo 'CANDIDATE_BUILD_FAILED' | tee ../evidence/verdict.txt
  exit 4
fi
echo 'BUILD_PASS_ONLY_RUNTIME_NOT_TESTED' | tee ../evidence/verdict.txt
