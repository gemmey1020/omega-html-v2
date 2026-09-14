#!/usr/bin/env python3
"""Build one validated standalone Omega HTML v2 artifact and its receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_intake import compile_text
from consolidation_config import resolve_profile, resolve_recipe
from render_artifact import load_bundle, render, truthlock
from validate_rendered_artifact import validate as validate_rendered

BUNDLE_FILES = ("truth-model.json", "reader-brief.json", "document-strategy.json", "authored-content.json", "composition-model.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(args) -> dict:
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory must be absent or empty: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        bundle_dir = stage / "semantic-bundle"
        bundle_dir.mkdir()
        profile = resolve_profile(args.profile)["id"]
        recipe = resolve_recipe(args.recipe)["id"]
        if args.bundle:
            input_mode = "bundle"
            source = args.bundle.resolve()
            for name in BUNDLE_FILES:
                shutil.copy2(source / name, bundle_dir / name)
            normalized = {"source_type": "bundle", "source_locator": str(source), "recipe": recipe, "profile": profile}
            (bundle_dir / "normalized-request.json").write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
        else:
            input_mode = args.source_type
            text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
            locator = "inline prompt" if args.text is not None else str(args.input.resolve())
            normalized = compile_text(text, bundle_dir, source_type=args.source_type, audience=args.audience,
                                      language=args.language, recipe=recipe, profile=profile,
                                      title=args.title, source_locator=locator)
        bundle = load_bundle(bundle_dir)
        semantic_errors = truthlock(bundle)
        if semantic_errors:
            raise ValueError("Semantic validation failed: " + json.dumps(semantic_errors, ensure_ascii=False))
        html_path = stage / "omega-report.html"
        html_text = render(bundle, profile)
        html_path.write_text(html_text, encoding="utf-8")
        rendered_errors = validate_rendered(html_text, bundle, profile)
        if rendered_errors:
            raise ValueError("Rendered validation failed: " + json.dumps(rendered_errors, ensure_ascii=False))
        receipt = {
            "schema_version": 1, "status": "PASS", "input_mode": input_mode,
            "profile": profile, "recipe": recipe,
            "validation": {"semantic": "PASS", "rendered": "PASS"},
            "artifact_sha256": sha256(html_path),
            "bundle_sha256": {name: sha256(bundle_dir / name) for name in BUNDLE_FILES},
            "artifact": "omega-report.html", "bundle": "semantic-bundle",
        }
        (stage / "build-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            output.rmdir()
        os.replace(stage, output)
        return {"status": "PASS", "html": str(output / "omega-report.html"),
                "bundle": str(output / "semantic-bundle"), "receipt": str(output / "build-receipt.json")}
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text")
    inputs.add_argument("--input", type=Path)
    inputs.add_argument("--bundle", type=Path)
    parser.add_argument("--source-type", choices=("prompt", "markdown"), default="markdown")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--recipe")
    parser.add_argument("--audience", default="executive leadership")
    parser.add_argument("--language", default="en")
    parser.add_argument("--title")
    return parser.parse_args()


def main() -> int:
    try:
        print(json.dumps(build(parse_args()), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
