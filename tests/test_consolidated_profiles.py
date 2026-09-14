import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "render_artifact.py"
BUNDLE = ROOT / "evals" / "bundles" / "ahs-en"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_artifact", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConsolidatedProfilesTest(unittest.TestCase):
    def test_every_canonical_profile_renders_with_geometry_metadata(self):
        renderer = load_renderer()
        bundle = renderer.load_bundle(BUNDLE)
        profiles = json.loads((ROOT / "config" / "profiles.json").read_text())["profiles"]
        geometries = set()
        for profile in profiles:
            output = renderer.render(bundle, profile["id"])
            self.assertIn(f'data-surface-profile="{profile["id"]}"', output)
            self.assertIn(f'name="omega:profile_geometry" content="{profile["geometry"]}"', output)
            self.assertIn(f'name="omega:profile_density" content="{profile["density"]}"', output)
            self.assertIn(f'name="omega:profile_hero" content="{profile["hero"]}"', output)
            self.assertIn('minimumVisibleMs = 1200', output)
            self.assertIn('rel="icon"', output)
            geometries.add(profile["geometry"])
        self.assertEqual(len(geometries), len(profiles))

    def test_aliases_resolve_to_canonical_profiles(self):
        renderer = load_renderer()
        bundle = renderer.load_bundle(BUNDLE)
        self.assertIn('data-surface-profile="omega-silver"', renderer.render(bundle, "silver"))
        self.assertIn('data-surface-profile="aion-cyan"', renderer.render(bundle, "aion"))
        self.assertIn('data-surface-profile="hints-core"', renderer.render(bundle, "hints"))

    def test_profiles_have_non_color_structural_rules(self):
        renderer = load_renderer()
        bundle = renderer.load_bundle(BUNDLE)
        outputs = {name: renderer.render(bundle, name) for name in ("omega-gold", "omega-cyan", "omega-silver", "aion-cyan", "hints-core")}
        markers = {
            "omega-gold": "profile-geometry--framed-editorial",
            "omega-cyan": "profile-geometry--decision-grid",
            "omega-silver": "profile-geometry--dense-evidence-atlas",
            "aion-cyan": "profile-geometry--command-console",
            "hints-core": "profile-geometry--reveal-panels",
        }
        for profile, marker in markers.items():
            self.assertIn(marker, outputs[profile])


if __name__ == "__main__":
    unittest.main()
