import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.render_artifact import load_bundle, render


class Wave6QualityTest(unittest.TestCase):
    def bundle(self, name):
        return load_bundle(ROOT / "evals" / "bundles" / name)

    def test_ahs_reconstructs_operational_facts_and_varied_states(self):
        truth = self.bundle("ahs")["truth"]
        claims = {claim["claim_id"]: claim for claim in truth["claims"]}
        self.assertEqual(sum(c.get("materiality") == "material" for c in truth["claims"]), 24)
        self.assertIn("AHS.FACT.LEGACY_USERS", claims)
        self.assertIn("20,789", claims["AHS.FACT.LEGACY_USERS"]["protected_tokens"])
        self.assertIn("AHS.FACT.RESTORE_STATUS", claims)
        self.assertNotEqual({c["closure_state"] for c in claims.values() if c["claim_id"].startswith("AHS.REQUIREMENT.")}, {"open"})
        self.assertTrue(all(c.get("source_refs") for c in claims.values()))

    def test_real_fixtures_do_not_stuff_context_free_tokens(self):
        proposal = self.bundle("proposal")
        technical = self.bundle("technical")
        self.assertEqual(proposal["reader"]["language"]["primary"], "en")
        self.assertTrue(all("100" not in block["text"] for block in proposal["authored"]["blocks"]))
        self.assertTrue(all("100" not in block["text"] for block in technical["authored"]["blocks"]))
        self.assertEqual(proposal["authored"]["blocks"][0].get("protected_spans", []), [])
        self.assertGreaterEqual(len(technical["truth"]["claims"]), 5)

    def test_intents_render_different_semantic_structures(self):
        bundle = self.bundle("technical")
        html = render(bundle, "omega-hud")
        self.assertIn("<table", html)
        self.assertIn("<pre", html)
        self.assertIn('data-presentation-intent="technical_annex"', html)
        self.assertIn('data-presentation-intent="source_ledger"', html)
        self.assertIn("<ol", html)
        self.assertIn("<dl", html)

    def test_rendered_html_contains_material_traceability(self):
        bundle = self.bundle("proposal")
        html = render(bundle, "omega-minimal")
        for block in bundle["authored"]["blocks"]:
            self.assertIn(f'data-copy-id="{block["copy_id"]}"', html)
        for claim in bundle["truth"]["claims"]:
            if claim.get("materiality") == "material":
                self.assertIn(f'data-claim-id="{claim["claim_id"]}"', html)

    def test_validator_rejects_unreachable_copy_and_foreign_theme(self):
        bundle = self.bundle("proposal")
        html = render(bundle, "omega-minimal").replace('data-copy-id="COPY.PROPOSAL.HEADLINE"', "").replace('data-copy-ref="COPY.PROPOSAL.HEADLINE"', "")
        html = html.replace('<meta name="omega:theme_profile" content="omega-minimal">', '<meta name="omega:theme_profile" content="omega-hud">')
        with self.subTest("validator CLI"):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                html_path = temp / "proposal.html"
                bundle_path = temp / "bundle"
                bundle_path.mkdir()
                html_path.write_text(html, encoding="utf-8")
                for key, filename in (("truth", "truth-model.json"), ("reader", "reader-brief.json"), ("strategy", "document-strategy.json"), ("authored", "authored-content.json"), ("composition", "composition-model.json")):
                    (bundle_path / filename).write_text(json.dumps(bundle[key], ensure_ascii=False), encoding="utf-8")
                result = subprocess.run([
                    sys.executable,
                    str(ROOT / "scripts" / "validate_rendered_artifact.py"),
                    "--html", str(html_path), "--bundle", str(bundle_path),
                ], capture_output=True, text=True)
                errors = json.loads(result.stdout)["errors"]
        codes = {error["code"] for error in errors}
        self.assertIn("MATERIAL_COPY_NOT_REACHABLE", codes)
        self.assertIn("THEME_PROFILE_MISMATCH", codes)

    def test_validator_accepts_generated_artifact_with_closed_trace_nodes(self):
        bundle = self.bundle("ahs")
        html = render(bundle, "omega-editorial")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            html_path = temp / "ahs.html"
            bundle_path = temp / "bundle"
            bundle_path.mkdir()
            html_path.write_text(html, encoding="utf-8")
            for key, filename in (("truth", "truth-model.json"), ("reader", "reader-brief.json"), ("strategy", "document-strategy.json"), ("authored", "authored-content.json"), ("composition", "composition-model.json")):
                (bundle_path / filename).write_text(json.dumps(bundle[key], ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([
                sys.executable,
                str(ROOT / "scripts" / "validate_rendered_artifact.py"),
                "--html", str(html_path), "--bundle", str(bundle_path),
                "--surface-profile", "omega-editorial",
            ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
