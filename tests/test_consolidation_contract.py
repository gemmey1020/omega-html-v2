import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "consolidation_config.py"


def load_module():
    spec = importlib.util.spec_from_file_location("consolidation_config", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("consolidation config module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConsolidationContractTest(unittest.TestCase):
    def test_profile_aliases_resolve_to_canonical_profiles(self):
        config = load_module()
        self.assertEqual(config.resolve_profile("cyan")["id"], "omega-cyan")
        self.assertEqual(config.resolve_profile("silver")["id"], "omega-silver")
        self.assertEqual(config.resolve_profile("hints")["id"], "hints-core")
        self.assertEqual(config.resolve_profile("aion")["id"], "aion-cyan")

    def test_recipe_defaults_follow_document_intent(self):
        config = load_module()
        self.assertEqual(config.resolve_recipe(None, "audit_report")["id"], "technical-audit")
        self.assertEqual(config.resolve_recipe(None, "proposal")["id"], "proposal")
        self.assertEqual(config.resolve_recipe(None, "executive_decision")["id"], "executive-decision")

    def test_profiles_expose_non_color_composition_traits(self):
        config = load_module()
        gold = config.resolve_profile("gold")
        cyan = config.resolve_profile("cyan")
        silver = config.resolve_profile("silver")
        self.assertNotEqual(gold["geometry"], cyan["geometry"])
        self.assertNotEqual(cyan["density"], silver["density"])
        self.assertNotEqual(gold["hero"], silver["hero"])

    def test_unknown_profile_and_recipe_are_rejected(self):
        config = load_module()
        with self.assertRaisesRegex(ValueError, "Unknown Omega HTML v2 profile"):
            config.resolve_profile("rainbow")
        with self.assertRaisesRegex(ValueError, "Unknown Omega HTML v2 recipe"):
            config.resolve_recipe("dashboard-everything", "report")


if __name__ == "__main__":
    unittest.main()
