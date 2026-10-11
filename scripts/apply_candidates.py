#!/usr/bin/env python3
"""Conservative transformations against exact pinned Arcane Git blobs.
Not an AI engine: no repository push or production repair.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass

VERSIONS = {
    "v2.10.2": {
        "commit": "670ee2b34ea7b0fb2917643229b6ce9070ee9742",
        "file_blobs": {
            "frontend/src/lib/components/mobile-nav/mobile-nav-item.svelte": "ad852f96016962278976d6ec93a15eb615b2e50a",
            "frontend/src/lib/components/mobile-nav/mobile-nav.svelte": "145dcfc25c1ddd5d7c096895d271fcc60c3ae638",
        },
    },
    "v2.12.0": {
        "commit": "3089c2ec4a56da5ca934c37778e6aeb2f539862d",
        "file_blobs": {
            "frontend/src/routes/(app)/containers/[containerId]/+page.svelte": "9bf9991db1dd6b95f0925b30f367079cbc57b208",
        },
    },
    "v2.14.0": {
        "commit": "89619a824ea71bd39cada912cdbe660ee4df7176",
        "file_blobs": {
            "frontend/src/lib/components/role-editor/role-editor.svelte": "0514e4b637efbebc86fae1ebe859151ff93ce96a",
        },
    },
}


@dataclass(frozen=True)
class Replacement:
    path: str
    needle: str
    replacement: str


ROLE = "frontend/src/lib/components/role-editor/role-editor.svelte"
NAV_ITEM = "frontend/src/lib/components/mobile-nav/mobile-nav-item.svelte"
NAV = "frontend/src/lib/components/mobile-nav/mobile-nav.svelte"
CONTAINER = "frontend/src/routes/(app)/containers/[containerId]/+page.svelte"

REPLACEMENTS = {
    "v2.12.0": [
        Replacement(
            CONTAINER,
            '{#snippet containerHeader(container: ContainerDetailsDto)}\n\t<div class="flex items-center gap-2">',
            '{#snippet containerHeader(container: ContainerDetailsDto)}\n\t<div class="flex min-w-0 flex-wrap items-center gap-2">',
        ),
    ],
    "v2.14.0": [
        Replacement(
            ROLE,
            'type="button"\n' + '\t'*7 + 'class="w-full"\n' + '\t'*7 + 'icon={CopyIcon}',
            'type="button"\n' + '\t'*7 + 'class="w-full h-auto! min-h-9 whitespace-normal! [&>span]:min-w-0 [&>span]:flex-wrap [&>span]:justify-center [&>span]:break-words"\n' + '\t'*7 + 'icon={CopyIcon}',
        ),
    ],
    "v2.10.2": [
        Replacement(
            NAV_ITEM,
            "'h-11 flex-col gap-0.5 overflow-hidden rounded-2xl px-2 py-1 sm:h-12 sm:min-w-[60px] sm:px-3 sm:py-1.5'",
            "'h-auto min-h-11 flex-col gap-0.5 overflow-visible rounded-2xl px-0.5 py-1 sm:h-12 sm:min-w-[60px] sm:px-3 sm:py-1.5'",
        ),
        Replacement(
            NAV_ITEM,
            '<span class="w-full truncate text-center text-[10px] leading-none font-normal text-muted-foreground">{item.title}</span>',
            '<span class="w-full text-center text-[10px] font-normal text-muted-foreground whitespace-normal break-normal leading-tight">{item.title}</span>',
        ),
        Replacement(
            NAV,
            "showLabels ? 'gap-1.5 px-2.5 py-1.5 sm:gap-2 sm:px-3 sm:py-2'",
            "showLabels ? 'gap-0.5 px-1 py-1.5 sm:gap-2 sm:px-3 sm:py-2'",
        ),
    ],
}


def shell(*args, cwd):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(args)} failed: {p.stderr}")
    return p.stdout.strip()


def replace_exact(content, old, new):
    if content.count(old) != 1:
        raise ValueError(f"Expected one source anchor; found {content.count(old)}")
    return content.replace(old, new, 1)


def prepare_patches(root: pathlib.Path, version: str, git_checks=True):
    cfg = VERSIONS[version]
    if git_checks:
        actual = shell("git", "rev-parse", "HEAD", cwd=root)
        if actual != cfg["commit"]:
            raise ValueError(f"Commit mismatch. Expected {cfg['commit']}, got {actual}")
        if shell("git", "status", "--porcelain", "--untracked-files=no", cwd=root):
            raise ValueError("Refusing to patch a dirty checkout")

    changes = {}
    for path, blob in cfg["file_blobs"].items():
        target = root / path
        content = target.read_text(encoding="utf-8")
        if git_checks:
            actual_blob = shell("git", "hash-object", path, cwd=root)
            if actual_blob != blob:
                raise ValueError(f"Git blob mismatch in {path}; expected {blob}, got {actual_blob}")
        new = content
        for op in REPLACEMENTS[version]:
            if op.path == path:
                new = replace_exact(new, op.needle, op.replacement)
        if new == content:
            raise ValueError(f"No changes to {path}")
        changes[path] = (content, new)
    return changes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--version", choices=list(VERSIONS), required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--manifest", default=None)
    args = p.parse_args()
    root = pathlib.Path(args.root).resolve()
    changes = prepare_patches(root, args.version)
    manifest = {
        "version": args.version, "pinned_commit": VERSIONS[args.version]["commit"],
        "status": "DRY_RUN" if args.dry_run else "PATCH_APPLIED_NOT_BUILT",
        "changed_files": [],
    }
    for path, (original, modified) in changes.items():
        manifest["changed_files"].append({
            "path": path,
            "sha256_before": hashlib.sha256(original.encode()).hexdigest(),
            "sha256_after": hashlib.sha256(modified.encode()).hexdigest(),
        })
    if not args.dry_run:
        for path, (_, modified) in changes.items():
            (root / path).write_text(modified, encoding="utf-8")
    if args.manifest:
        pathlib.Path(args.manifest).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"REFUSED: {ex}", file=sys.stderr)
        raise SystemExit(2)
