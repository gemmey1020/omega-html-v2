import base64
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.render_artifact import THEMES, load_bundle, render


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

    def test_executive_hud_shell_adds_traceable_signal_layer(self):
        for name, profile in (("ahs", "omega-gold"), ("proposal", "omega-minimal"), ("technical", "omega-hud")):
            with self.subTest(name=name):
                html = render(self.bundle(name), profile)
                self.assertIn('class="hud-topbar"', html)
                self.assertIn('class="hero-surface"', html)
                self.assertIn('class="hud-metrics"', html)
                self.assertGreaterEqual(html.count('class="hud-signal"'), 3)
                self.assertIn('data-structured-id=', html)
                self.assertIn('data-copy-ref=', html)

    def test_screen_first_hud_has_depth_motion_and_reduced_motion_guard(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for token in (
            "perspective:",
            "transform-style:",
            "transition:",
            "@keyframes",
            ":hover",
            "prefers-reduced-motion",
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_screen_sections_have_varied_card_treatments(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for token in (
            ".hud-page .section {",
            ".hud-page .section--verdict",
            ".hud-page .section--sequence",
            ".hud-page .section--technical_annex",
            "border-radius:var(--hud-radius-lg)",
            "border-radius:var(--hud-radius-md)",
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_ahs_hud_promotes_four_traceable_decision_signals(self):
        html = render(self.bundle("ahs"), "omega-gold")
        self.assertEqual(html.count('class="hud-signal"'), 4)

    def test_fact_cards_reserve_readable_title_and_text_spacing(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for token in (
            ".structured--facts .structured-title {grid-column:1 / -1",
            ".hud-page .structured--facts {padding-top:",
            ".hud-page .fact {padding-block:",
            ".hud-page .fact dd {line-height:",
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_screen_colorways_stay_dark_and_cohesive(self):
        def luminance(color):
            rgb = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

        for profile in ("omega-gold", "omega-teal", "omega-cyan"):
            with self.subTest(profile=profile):
                self.assertLess(luminance(THEMES[profile]["surface"]), 0.10)
                self.assertLess(luminance(THEMES[profile]["soft"]), 0.16)
                self.assertLess(luminance(THEMES[profile]["line"]), 0.25)

    def test_authored_copy_avoids_template_like_openers(self):
        banned = (
            "المصدر يوضح",
            "هذه المراجعة تلتقط",
            "A bounded pilot answers",
            "Before committing to full production",
        )
        for name in ("ahs", "proposal", "technical"):
            bundle = self.bundle(name)
            texts = [block.get("text", "") for block in bundle["authored"]["blocks"]]
            rendered = render(bundle, "omega-gold" if name == "ahs" else ("omega-minimal" if name == "proposal" else "omega-hud"))
            for phrase in banned:
                with self.subTest(name=name, phrase=phrase):
                    self.assertFalse(any(phrase in text for text in texts))
                    self.assertNotIn(phrase, rendered)

    def test_ahs_public_artifact_excludes_internal_execution_sequence(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for token in (
            'class="section section--sequence"',
            "ترتيب الإغلاق الذي يحمي القرار",
            "طابق الهوية",
            'data-copy-id="COPY.AHS.TECH"',
            'class="section section--technical_annex"',
            "أمر الفحص المرصود",
            "سجل المصدر",
            "سجل المصادر",
            "الخطوات التالية",
            "تفعيل الحزمة",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, html)

    def test_ahs_favicon_is_the_omega_mark(self):
        html = render(self.bundle("ahs"), "omega-gold")
        match = re.search(r'<link rel="icon" href="data:image/svg\+xml;base64,([^"]+)"', html)
        self.assertIsNotNone(match)
        icon_svg = base64.b64decode(match.group(1)).decode("utf-8")
        self.assertIn("Ω", icon_svg)
        self.assertNotIn("M16 32h32M32 16v32", icon_svg)

    def test_favicon_uses_the_active_theme_accent(self):
        for profile in ("omega-gold", "omega-teal", "omega-cyan"):
            with self.subTest(profile=profile):
                html = render(self.bundle("ahs"), profile)
                match = re.search(r'<link rel="icon" href="data:image/svg\+xml;base64,([^"]+)"', html)
                self.assertIsNotNone(match)
                icon_svg = base64.b64decode(match.group(1)).decode("utf-8")
                self.assertIn(THEMES[profile]["accent"], icon_svg)

    def test_every_surface_has_a_branded_self_dismissing_preloader(self):
        for name, profile in (("ahs", "omega-gold"), ("proposal", "omega-minimal"), ("technical", "omega-hud")):
            with self.subTest(name=name):
                html = render(self.bundle(name), profile)
                self.assertIn('id="omega-preloader"', html)
                self.assertIn('class="omega-preloader"', html)
                self.assertIn("Ω OMEGA", html)
                self.assertIn("Jemy", html)
                self.assertIn("omega-preloader--hidden", html)
                self.assertIn("DOMContentLoaded", html)
                self.assertIn("minimumVisibleMs", html)
                self.assertIn("performance.now()", html)
                self.assertIn("setTimeout", html)
                self.assertIn("omega-ready", html)
                self.assertIn("@keyframes omega-preloader-in {from {transform:", html)
                self.assertIn("@media print", html)
                self.assertIn(".omega-preloader", html)

    def test_ahs_public_artifact_states_unknown_migration_target(self):
        bundle = self.bundle("ahs")
        html = render(bundle, "omega-gold")
        self.assertIn("الخادم القديم", html)
        self.assertIn("خادم إنتاج جديد", html)
        self.assertIn("هوية أو مواصفات أو نقطة وصول", html)
        self.assertIn("وجهة الترحيل غير معروفة", html)
        self.assertNotIn("srv981087", html)

    def test_ahs_public_artifact_exposes_conditional_effort_modes_and_hours(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for token in ("Light", "Medium", "Hard", "6h/day", "10h/day", "12h/day peak", "120h"):
            with self.subTest(token=token):
                self.assertIn(token, html)
        self.assertIn('data-section-id="effort"', html)
        self.assertIn('data-presentation-intent="comparison"', html)
        self.assertIn("ليست موعدًا مضمونًا", html)

    def test_ahs_promotes_effort_snapshot_near_the_top(self):
        html = render(self.bundle("ahs"), "omega-gold")
        section_ids = re.findall(r'data-section-id="([^"]+)"', html)
        self.assertEqual(section_ids[0], "decision")
        self.assertLessEqual(section_ids.index("effort"), 1)
        self.assertIn('data-visual-treatment="mode-snapshot"', html)
        self.assertIn('class="effort-snapshot"', html)

    def test_ahs_renders_source_backed_metrics_as_big_number_cards(self):
        html = render(self.bundle("ahs"), "omega-gold")
        self.assertIn('data-visual-treatment="metrics"', html)
        self.assertIn('class="metric-grid"', html)
        self.assertGreaterEqual(html.count('class="metric-card"'), 7)
        for value in ("20,789", "71", "28", "62", "227", "24", "120h"):
            with self.subTest(value=value):
                self.assertIn(f'data-metric-value="{value}"', html)

    def test_ahs_has_a_conditional_timeline_with_status_states(self):
        html = render(self.bundle("ahs"), "omega-gold")
        self.assertIn('data-section-id="timeline"', html)
        self.assertIn('data-presentation-intent="timeline"', html)
        self.assertIn('class="structured structured--timeline"', html)
        self.assertGreaterEqual(len(re.findall(r'class="timeline-step(?:\s|\")', html)), 4)
        for status in ("مُثبت", "مفتوح", "محجوب", "مشروط"):
            with self.subTest(status=status):
                self.assertIn(status, html)
        self.assertNotIn("2026-09-", html)

    def test_ahs_uses_distinct_visual_treatments_and_a_refined_footer(self):
        html = render(self.bundle("ahs"), "omega-gold")
        for treatment in ("verdict", "mode-snapshot", "metrics", "timeline", "matrix"):
            with self.subTest(treatment=treatment):
                self.assertIn(f'data-visual-treatment="{treatment}"', html)
        self.assertIn('class="hud-footer"', html)
        self.assertIn('class="footer-mark"', html)
        self.assertIn("AHS · قراءة تنفيذية مستقلة", html)

    def test_effort_snapshot_allows_its_mode_cards_to_fit_the_section(self):
        html = render(self.bundle("ahs"), "omega-gold")
        self.assertIn('.hud-page .section--comparison .structured--effort {height:auto}', html)
        self.assertIn('.hud-page .section--comparison .section-body {display:flex', html)

    def test_evidence_groups_have_more_than_one_layout_archetype(self):
        html = render(self.bundle("ahs"), "omega-gold")
        self.assertIn('.hud-page .section--operations .section-heading {order:2', html)
        self.assertIn('.hud-page .section--content {display:block', html)
        self.assertIn('.hud-page .section--content .section-heading {display:flex', html)


if __name__ == "__main__":
    unittest.main()
