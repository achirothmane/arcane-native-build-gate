#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${GITHUB_WORKSPACE:-$PWD}"
mkdir -p "$ROOT/evidence"
cd "$ROOT/arcane"
export CI=true
pnpm install --frozen-lockfile > "$ROOT/evidence/pnpm-install.txt" 2>&1
pnpm -C tests exec playwright install --with-deps chromium > "$ROOT/evidence/playwright-install.txt" 2>&1
cp "$ROOT/experiment/runtime/lrg.config.ts" tests/lrg.config.ts
cp "$ROOT/experiment/runtime/lrg_runtime.spec.ts" tests/lrg_runtime.spec.ts
cleanup() {
  docker logs lrg_arcane > "$ROOT/evidence/server-end.log" 2>&1 || true
  docker rm -f lrg_arcane >/dev/null 2>&1 || true
}
trap cleanup EXIT
run_case() {
  local variant="$1"
  local tag="lrg-arcane:$variant"
  docker rm -f lrg_arcane >/dev/null 2>&1 || true
  echo "Building native image: $variant"
  if ! docker build -f docker/Dockerfile --tag "$tag" . > "$ROOT/evidence/docker-build-$variant.log" 2>&1; then
    echo "DOCKER_BUILD_FAILED:$variant" | tee -a "$ROOT/evidence/verdict.txt"
    return 1
  fi
  docker run -d --name lrg_arcane -p 3000:3552 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e APP_ENV=test -e ENVIRONMENT=testing \
    -e APP_URL=http://127.0.0.1:3000 \
    -e ENCRYPTION_KEY=3JDIgolks2tJ9ymm1AdqzlYMWu0DUWyt \
    -e JWT_SECRET=your-super-secret-jwt-key-change-this-in-production \
    -e PUID=65532 -e PGID=65532 \
    "$tag" >/dev/null
  local ok=0
  for i in $(seq 1 100); do
    if curl -fsS http://127.0.0.1:3000/login >/dev/null 2>&1; then ok=1; break; fi
    sleep 2
  done
  docker logs lrg_arcane > "$ROOT/evidence/server-$variant.log" 2>&1 || true
  if [[ "$ok" != 1 ]]; then
    echo "SERVER_NOT_READY:$variant" | tee -a "$ROOT/evidence/verdict.txt"
    return 1
  fi
  export VARIANT="$variant" EVIDENCE_DIR="$ROOT/evidence" PW_JSON="$ROOT/evidence/playwright-$variant.json"
  set +e
  pnpm -C tests exec playwright test --config lrg.config.ts lrg_runtime.spec.ts > "$ROOT/evidence/playwright-$variant.log" 2>&1
  local code=$?
  set -e
  docker logs lrg_arcane > "$ROOT/evidence/server-$variant.log" 2>&1 || true
  docker rm -f lrg_arcane >/dev/null 2>&1 || true
  echo "PLAYWRIGHT_EXIT:$variant:$code" | tee -a "$ROOT/evidence/verdict.txt"
  return "$code"
}
if ! run_case baseline; then
  echo "STOP: BASELINE_APP_TEST_UNAVAILABLE" | tee -a "$ROOT/evidence/verdict.txt"
  exit 11
fi
python3 "$ROOT/experiment/scripts/apply_candidates.py" --root "$ROOT/arcane" --version v2.10.2 --manifest "$ROOT/evidence/runtime-patch-manifest.json" > "$ROOT/evidence/patch-application.log" 2>&1
git diff --check
git diff -- frontend/src/ > "$ROOT/evidence/runtime-original-to-candidate.diff"
if ! run_case candidate; then
  echo "STOP: CANDIDATE_APP_TEST_UNAVAILABLE" | tee -a "$ROOT/evidence/verdict.txt"
  exit 12
fi
python3 "$ROOT/experiment/runtime/evaluate.py" "$ROOT/evidence/baseline-french-mobile.json" "$ROOT/evidence/candidate-french-mobile.json" > "$ROOT/evidence/runtime-conclusion.json"
cat "$ROOT/evidence/runtime-conclusion.json"
