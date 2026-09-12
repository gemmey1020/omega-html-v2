import json
import unittest
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures" / "core-contracts"


class CoreContractsTest(unittest.TestCase):
    schema_names = ["truth-model", "reader-brief", "document-strategy", "authored-content", "composition-model"]

    def load(self, name):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def validate(self, stem, fixture):
        schema = json.loads((SCHEMAS / f"{stem}.schema.json").read_text())
        return Draft202012Validator(schema).iter_errors(fixture)

    def test_schemas_are_2020_12_json(self):
        for name in self.schema_names:
            data = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
            self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_valid_fixtures_validate(self):
        for stem in self.schema_names:
            self.assertEqual(list(self.validate(stem, self.load(f"{stem}.json"))), [])

    def test_truth_rejects_presentation_leakage(self):
        bad = deepcopy(self.load("truth-model.json")); bad["theme"] = "gold"; bad["claims"][0]["card"] = True
        self.assertTrue(list(self.validate("truth-model", bad)))

    def test_composition_rejects_raw_styling(self):
        bad = deepcopy(self.load("composition-model.json")); bad["sections"][0]["css"] = "color:red"
        self.assertTrue(list(self.validate("composition-model", bad)))

    def test_reader_rejects_malformed_language(self):
        bad = deepcopy(self.load("reader-brief.json")); bad["language"] = {"foo": 123}
        self.assertTrue(list(self.validate("reader-brief", bad)))

    def test_reference_arrays_reject_non_string_ids(self):
        bad = deepcopy(self.load("authored-content.json")); bad["blocks"][0]["claim_refs"] = [7]
        self.assertTrue(list(self.validate("authored-content", bad)))

    def test_unknown_top_level_fields_rejected(self):
        bad = deepcopy(self.load("document-strategy.json")); bad["surprise"] = True
        self.assertTrue(list(self.validate("document-strategy", bad)))

    def test_truth_has_no_presentation_fields(self):
        raw = json.dumps(self.load("truth-model.json"))
        for field in ("theme", "css", "card", "layout", "visual_component", "reader_copy"):
            self.assertNotIn(f'"{field}"', raw)

    def test_material_claim_refs_exist(self):
        claims = {c["claim_id"] for c in self.load("truth-model.json")["claims"]}
        for block in self.load("authored-content.json")["blocks"]:
            for ref in block["claim_refs"]:
                self.assertIn(ref, claims)

    def test_copy_refs_exist(self):
        copies = {b["copy_id"] for b in self.load("authored-content.json")["blocks"]}
        for section in self.load("composition-model.json")["sections"]:
            for ref in section["copy_refs"]:
                self.assertIn(ref, copies)

    def test_composition_has_no_raw_markup(self):
        raw = json.dumps(self.load("composition-model.json"))
        self.assertNotRegex(raw, r"<[^>]+>|\bCSS\b|style=")

    def test_reader_separates_intent_and_surface(self):
        data = self.load("reader-brief.json")
        self.assertIn("document_intent", data)
        self.assertIn("surface_profile", data)
        self.assertNotEqual(data["document_intent"], data["surface_profile"])

    def test_states_are_separate(self):
        truth = self.load("truth-model.json")["claims"][0]
        self.assertIn("epistemic_state", truth)
        self.assertIn("closure_state", truth)
        self.assertIn("risk", truth)

    def test_gate1_foundation_still_exists(self):
        self.assertTrue((ROOT / "manifests" / "v1-manifest.tsv").is_file())
        self.assertFalse(Path("/home/jemy/.codex/skills/omega-html/SKILL.md").resolve().samefile(ROOT / "SKILL.md"))


if __name__ == "__main__":
    unittest.main()
