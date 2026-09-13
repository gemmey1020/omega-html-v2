#!/usr/bin/env python3
import argparse
import html.parser
import json
import re
import sys
from pathlib import Path

PROFILES = {"omega-editorial", "omega-minimal", "omega-hud", "aion", "omega-gold", "omega-teal", "omega-cyan"}


class ArtifactParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.attrs = []
        self.text = []
        self.copy_ids = set()
        self.claim_ids = set()
        self.section_ids = set()
        self.structured_ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append(tag)
        self.attrs.append(values)
        if values.get("data-copy-id"):
            self.copy_ids.update(values["data-copy-id"].split())
        if values.get("data-copy-ref"):
            self.copy_ids.update(values["data-copy-ref"].split())
        if values.get("data-claim-id"):
            self.claim_ids.update(values["data-claim-id"].split())
        if values.get("data-section-id"):
            self.section_ids.add(values["data-section-id"])
        if values.get("data-structured-id"):
            self.structured_ids.add(values["data-structured-id"])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        # Keep the complete start-tag ledger.  Validation needs attributes from
        # closed elements too (copy/claim trace markers and metadata), so this
        # parser intentionally does not treat ``tags`` as an open-element stack.
        return None

    def handle_data(self, data):
        self.text.append(data)


def error(code, detail):
    return {"code": code, "detail": detail}


def validate(html_text, bundle, expected_profile=None):
    errors = []
    parser = ArtifactParser()
    try:
        parser.feed(html_text)
        parser.close()
    except html.parser.HTMLParseError as exc:
        errors.append(error("HTML_PARSE_ERROR", str(exc)))
    if not re.match(r"^\s*<!doctype\s+html", html_text, re.I):
        errors.append(error("REQUIRED_HTML_STRUCTURE", "doctype html"))
    for tag in ("html", "head", "body", "main", "header", "footer"):
        if tag not in parser.tags and not re.search(fr"<{tag}\b", html_text, re.I):
            errors.append(error("REQUIRED_HTML_STRUCTURE", tag))
    meta = {values.get("name"): values.get("content") for tag, values in zip(parser.tags, parser.attrs) if tag == "meta" and values.get("name")}
    root_match = re.search(r"<html\b([^>]*)>", html_text, re.I)
    root_attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', root_match.group(1))) if root_match else {}
    profile = meta.get("omega:theme_profile")
    if not profile:
        errors.append(error("METADATA_MISSING", "omega:theme_profile"))
    if not meta.get("omega:language") or not meta.get("omega:direction"):
        errors.append(error("METADATA_MISSING", "omega:language/omega:direction"))
    if expected_profile and profile != expected_profile:
        errors.append(error("THEME_PROFILE_MISMATCH", f"expected {expected_profile}, got {profile}"))
    if profile and root_attrs.get("data-surface-profile") != profile:
        errors.append(error("THEME_PROFILE_MISMATCH", "root data-surface-profile differs from metadata"))
    if root_attrs.get("lang") != meta.get("omega:language") or root_attrs.get("dir") != meta.get("omega:direction"):
        errors.append(error("LANGUAGE_DIRECTION_MISMATCH", "html attributes differ from metadata"))
    if "@media print" not in html_text:
        errors.append(error("PRINT_STYLESHEET_MISSING", "@media print"))
    if re.search(r"https?://|url\s*\(", html_text, re.I):
        errors.append(error("REMOTE_DEPENDENCY", "remote URL or CSS url()"))
    if "{{" in html_text or "}}" in html_text:
        errors.append(error("UNRESOLVED_TEMPLATE", "template marker"))
    if profile in PROFILES:
        for foreign in PROFILES - {profile}:
            if re.search(fr"(?:meta[^>]+content=|data-[\w-]+=)[\"'][^\"']*{re.escape(foreign)}", html_text, re.I):
                errors.append(error("FOREIGN_THEME_MARKER", foreign))
    composed_copy_ids = {ref for section in bundle["composition"]["sections"] for ref in section.get("copy_refs", [])}
    for section in bundle["composition"]["sections"]:
        for block in section.get("structured_blocks", []):
            composed_copy_ids.update(block.get("copy_refs", []))
            composed_copy_ids.update(ref for item in block.get("items", []) for ref in item.get("copy_refs", []))
            composed_copy_ids.update(ref for row in block.get("rows", []) for ref in row.get("copy_refs", []))
    rendered_copy_ids = parser.copy_ids
    for copy_id in sorted(composed_copy_ids - rendered_copy_ids):
        errors.append(error("MATERIAL_COPY_NOT_REACHABLE", copy_id))
    material_claims = {claim["claim_id"] for claim in bundle["truth"]["claims"] if claim.get("materiality") == "material"}
    for claim_id in sorted(material_claims - parser.claim_ids):
        errors.append(error("MATERIAL_CLAIM_NOT_TRACEABLE", claim_id))
    visible_text = "".join(parser.text)
    for claim in bundle["truth"]["claims"]:
        for token in claim.get("protected_tokens", []):
            if token not in visible_text:
                errors.append(error("PROTECTED_TOKEN_MISSING", token))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--surface-profile", default=None)
    args = parser.parse_args()
    try:
        html_text = Path(args.html).read_text(encoding="utf-8")
        bundle_dir = Path(args.bundle)
        names = {"truth": "truth-model", "reader": "reader-brief", "strategy": "document-strategy", "authored": "authored-content", "composition": "composition-model"}
        bundle = {key: json.loads((bundle_dir / f"{name}.json").read_text(encoding="utf-8")) for key, name in names.items()}
        errors = validate(html_text, bundle, args.surface_profile)
    except (OSError, ValueError) as exc:
        errors = [error("ARTIFACT_INPUT_ERROR", str(exc))]
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, ensure_ascii=False))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
