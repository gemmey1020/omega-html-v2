#!/usr/bin/env python3
"""Resolve canonical Omega HTML v2 profiles and composition recipes."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _load(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))

def resolve_profile(value: str) -> dict:
    requested = value.strip().lower()
    for profile in _load("profiles.json")["profiles"]:
        if requested == profile["id"] or requested in profile.get("aliases", []):
            return profile
    raise ValueError(f"Unknown Omega HTML v2 profile: {value}")

def resolve_recipe(value: str | None, document_intent: str = "report") -> dict:
    config = _load("recipes.json")
    requested = value or config["intent_defaults"].get(document_intent, "executive-decision")
    for recipe in config["recipes"]:
        if requested == recipe["id"]:
            return recipe
    raise ValueError(f"Unknown Omega HTML v2 recipe: {requested}")
