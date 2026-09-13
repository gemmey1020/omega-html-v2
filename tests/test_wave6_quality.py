import json
import re
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

    def test_visual_recovery_uses_document_specific_full_width_layouts(self):
        ahs = render(self.bundle("ahs"), "omega-editorial")
        proposal = render(self.bundle("proposal"), "omega-minimal")
        technical = render(self.bundle("technical"), "omega-hud")
        self.assertIn('data-document-kind="audit"', ahs)
        self.assertIn('class="document-grid document-grid--audit"', ahs)
        self.assertNotIn('class="rail"', ahs)
        self.assertIn('data-document-kind="proposal"', proposal)
        self.assertIn('class="document-grid document-grid--proposal"', proposal)
        self.assertIn('data-document-kind="technical"', technical)
        self.assertIn('class="document-grid document-grid--technical"', technical)
        self.assertNotEqual(ahs.split('<main', 1)[1].split('</main>', 1)[0], proposal.split('<main', 1)[1].split('</main>', 1)[0])

    def test_arabic_technical_surface_localizes_generic_labels(self):
        html = render(self.bundle("technical"), "omega-hud")
        for label in ("Environment", "Evidence status", "Observed command", "Release caveat", "Technical annex", "Source ledger"):
            self.assertNotIn(f">{label}<", html)

    def test_proposal_surface_keeps_one_language(self):
        html = render(self.bundle("proposal"), "omega-minimal")
        self.assertIsNone(re.search(r"[\u0600-\u06ff]", html))

    def test_hud_colorway_comparisons_preserve_semantic_layout(self):
        bundle = self.bundle("ahs")
        base = render(bundle, "omega-editorial")
        for profile in ("omega-gold", "omega-teal", "omega-cyan"):
            with self.subTest(profile=profile):
                html = render(bundle, profile)
                self.assertIn(f'data-surface-profile="{profile}"', html)
                self.assertIn(f'<meta name="omega:theme_profile" content="{profile}">', html)
                self.assertIn('data-document-kind="audit"', html)
                self.assertIn('class="document-grid document-grid--audit"', html)
                self.assertIn('data-claim-id="AHS.FACT.RESTORE_STATUS"', html)
                self.assertNotEqual(html, base)


if __name__ == "__main__":
    unittest.main()
