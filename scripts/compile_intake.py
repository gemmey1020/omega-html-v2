#!/usr/bin/env python3
"""Compile prompt or conservative Markdown into an Omega HTML v2 semantic bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from consolidation_config import resolve_profile, resolve_recipe


STATE_PREFIXES = {
    "VERIFIED": ("observed", "verified", "low"),
    "USER-STATED": ("source_backed", "open", "medium"),
    "UNKNOWN": ("unknown", "open", "unspecified"),
    "INFERRED": ("inferred", "partial", "medium"),
    "NOT-FOUND": ("not_found", "open", "high"),
    "CONFLICT": ("inferred", "open", "high"),
}


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stable_id(prefix: str, text: str, index: int) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}.{index:03d}.{digest}"


def _state(text: str) -> tuple[str, str, str, str]:
    match = re.match(r"^([A-Za-z-]+):\s*(.*)$", text.strip(), re.S)
    if match and match.group(1).upper() in STATE_PREFIXES:
        epistemic, closure, risk = STATE_PREFIXES[match.group(1).upper()]
        return match.group(2).strip(), epistemic, closure, risk
    return text.strip(), "source_backed", "open", "medium"


def _parse_markdown(text: str) -> tuple[str | None, list[dict]]:
    title = None
    records: list[dict] = []
    section = "Overview"
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
            i += 1
            continue
        if line.startswith("## "):
            section = line[3:].strip()
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-+", lines[i + 1].strip()):
            table_lines = [line]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in row.strip("|").split("|")] for row in table_lines]
            records.append({"kind": "table", "section": section, "columns": cells[0], "rows": cells[1:]})
            continue
        if line.startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            records.append({"kind": "list", "section": section, "items": items})
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "- ", "* ", "|")):
            paragraph.append(lines[i].strip())
            i += 1
        records.append({"kind": "paragraph", "section": section, "text": " ".join(paragraph)})
    return title, records


def compile_text(source: str, output_dir: Path, *, source_type: str, audience: str,
                 language: str, recipe: str | None, profile: str, title: str | None,
                 source_locator: str) -> dict:
    if not source.strip():
        raise ValueError("Input text is empty")
    if source_type not in {"prompt", "markdown"}:
        raise ValueError(f"Unsupported source type: {source_type}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_profile = resolve_profile(profile)
    selected_recipe = resolve_recipe(recipe)
    parsed_title, records = _parse_markdown(source)
    document_title = title or parsed_title or "Omega Report"
    direction = "rtl" if language.lower().startswith("ar") else "ltr"
    source_id = "SOURCE.INTAKE.001"
    claims, blocks, sections = [], [], []
    claim_no = copy_no = block_no = 0

    def add_claim(raw: str, *, material: bool = False) -> tuple[str, str]:
        nonlocal claim_no, copy_no
        meaning, epistemic, closure, risk = _state(raw)
        claim_no += 1
        copy_no += 1
        claim_id = _stable_id("CLAIM.INTAKE", meaning, claim_no)
        copy_id = _stable_id("COPY.INTAKE", meaning, copy_no)
        claims.append({"claim_id": claim_id, "meaning": meaning, "epistemic_state": epistemic,
                       "closure_state": closure, "risk": risk, "source_refs": [source_id],
                       "protected_tokens": [], "materiality": "material" if material else "supporting"})
        blocks.append({"copy_id": copy_id, "role": "paragraph", "text": meaning,
                       "claim_refs": [claim_id], "protected_spans": []})
        return claim_id, copy_id

    first_claim = True
    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(record["section"], []).append(record)

    for section_name, section_records in grouped.items():
        section_claims, section_copies, structured = [], [], []
        for record in section_records:
            if record["kind"] == "paragraph":
                cid, xid = add_claim(record["text"], material=first_claim)
                first_claim = False
                section_claims.append(cid); section_copies.append(xid)
            elif record["kind"] == "list":
                items = []
                for item in record["items"]:
                    cid, xid = add_claim(item, material=first_claim)
                    first_claim = False
                    section_claims.append(cid); section_copies.append(xid)
                    items.append({"label": item, "value": "Included", "claim_refs": [cid], "copy_refs": [xid]})
                block_no += 1
                structured.append({"block_id": f"STRUCT.INTAKE.{block_no:03d}", "type": "checklist",
                                   "title": section_name, "items": items})
            else:
                rows = []
                for row in record["rows"]:
                    text = " | ".join(row)
                    cid, xid = add_claim(text, material=first_claim)
                    first_claim = False
                    section_claims.append(cid); section_copies.append(xid)
                    rows.append({"cells": row, "claim_refs": [cid], "copy_refs": [xid]})
                block_no += 1
                structured.append({"block_id": f"STRUCT.INTAKE.{block_no:03d}", "type": "table",
                                   "title": section_name, "columns": record["columns"], "rows": rows})
        sections.append({"section_id": _stable_id("SECTION.INTAKE", section_name, len(sections)+1),
                         "purpose": section_name, "copy_refs": section_copies,
                         "claim_refs": section_claims, "presentation_intent": "table" if any(x["type"] == "table" for x in structured) else "narrative",
                         "structured_blocks": structured})

    truth = {"sources": [{"source_id": source_id, "description": f"{source_type} intake", "locator": source_locator}], "claims": claims}
    document_intent = selected_recipe["id"].replace("-", "_")
    journey = selected_recipe.get("journey", ["verdict", "evidence_matrix", "checklist"])
    reader = {"audience": audience, "document_intent": document_intent,
              "surface_profile": selected_profile["id"], "primary_question": document_title,
              "desired_action": "Review and decide", "technical_depth": "as supplied",
              "annex_policy": "Use only when the selected recipe requires it",
              "summary_rail": {"enabled": True, "title": document_title, "body": claims[0]["meaning"] if claims else ""},
              "language": {"primary": language, "direction": direction, "technical_english": "preserve exact identifiers"}}
    strategy = {"document_intent": document_intent, "through_line": claims[0]["meaning"] if claims else document_title,
                "must_appear_first": journey[:1],
                "secondary_content": journey[1:], "annex_content": [],
                "detail_level": selected_recipe.get("density", "balanced"),
                "uncertainty_policy": "Preserve supplied evidence state; never upgrade a claim silently",
                "reader_journey": journey}
    authored = {"blocks": blocks}
    composition = {"sections": sections}
    normalized = {"source_type": source_type, "source_locator": source_locator, "title": document_title,
                  "audience": audience, "language": language, "direction": direction,
                  "recipe": selected_recipe["id"], "profile": selected_profile["id"],
                  "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()}
    for name, value in (("truth-model.json", truth), ("reader-brief.json", reader),
                        ("document-strategy.json", strategy), ("authored-content.json", authored),
                        ("composition-model.json", composition), ("normalized-request.json", normalized)):
        _write(output_dir / name, value)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text")
    inputs.add_argument("--input", type=Path)
    parser.add_argument("--source-type", choices=("prompt", "markdown"), default="markdown")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--audience", default="executive leadership")
    parser.add_argument("--language", default="en")
    parser.add_argument("--recipe")
    parser.add_argument("--profile", default="cyan")
    parser.add_argument("--title")
    args = parser.parse_args()
    text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
    result = compile_text(text, args.output_dir, source_type=args.source_type, audience=args.audience,
                          language=args.language, recipe=args.recipe, profile=args.profile,
                          title=args.title, source_locator="inline prompt" if args.text is not None else str(args.input.resolve()))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
