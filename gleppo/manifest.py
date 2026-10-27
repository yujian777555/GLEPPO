"""Manifest build/verify: SHA256 freeze of task splits. Family C is written but never executed."""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Dict, List, Optional

from .tasks import SPLIT_SPEC, generate_split, attach_checker

MANIFEST_VERSION = "manifest-v1"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifests(data_dir: str) -> Dict[str, str]:
    os.makedirs(data_dir, exist_ok=True)
    manifest: dict = {
        "manifest_version": MANIFEST_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generator": "gleppo.tasks.generate_split",
        "splits": {},
    }
    for split_name, spec in SPLIT_SPEC.items():
        tasks = generate_split(
            family=spec["family"],
            prefix=spec["prefix"],
            n=spec["n"],
            seed_start=spec["seed_start"],
            templates=spec["templates"],
        )
        path = os.path.join(data_dir, f"{split_name}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for t in tasks:
                f.write(json.dumps(t, sort_keys=True, ensure_ascii=False) + "\n")
        digest = _sha256_file(path)
        manifest["splits"][split_name] = {
            "family": spec["family"],
            "n": spec["n"],
            "seed_start": spec["seed_start"],
            "templates": spec["templates"],
            "path": os.path.relpath(path, data_dir).replace("\\", "/"),
            "sha256": digest,
        }
    mpath = os.path.join(data_dir, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return {name: s["sha256"] for name, s in manifest["splits"].items()}


def verify_manifest(data_dir: str) -> List[str]:
    """Return list of errors; empty = OK."""
    errors: List[str] = []
    mpath = os.path.join(data_dir, "manifest.json")
    if not os.path.exists(mpath):
        return ["manifest.json missing"]
    with open(mpath, encoding="utf-8") as f:
        manifest = json.load(f)
    for name, meta in manifest.get("splits", {}).items():
        path = os.path.join(data_dir, meta["path"])
        if not os.path.exists(path):
            errors.append(f"{name}: file missing")
            continue
        digest = _sha256_file(path)
        if digest != meta["sha256"]:
            errors.append(f"{name}: sha256 mismatch (expected {meta['sha256'][:12]}... got {digest[:12]}...)")
        # count lines
        with open(path, encoding="utf-8") as f:
            n = sum(1 for _ in f)
        if n != meta["n"]:
            errors.append(f"{name}: line count {n} != {meta['n']}")
    return errors


def load_split(data_dir: str, split_name: str, with_checker: bool = True) -> List[dict]:
    mpath = os.path.join(data_dir, "manifest.json")
    with open(mpath, encoding="utf-8") as f:
        manifest = json.load(f)
    meta = manifest["splits"][split_name]
    path = os.path.join(data_dir, meta["path"])
    tasks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = json.loads(line)
            if with_checker:
                t = attach_checker(t)
            tasks.append(t)
    return tasks


class FamilyCGuard:
    """Runtime guard: raises if code paths attempt to evaluate Family C."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.violations: List[str] = []

    def check_task(self, task: dict) -> None:
        if self.enabled and task.get("family") == "C":
            msg = f"Family C access attempted: {task.get('task_id')}"
            self.violations.append(msg)
            raise PermissionError(msg)
