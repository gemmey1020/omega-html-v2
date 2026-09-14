import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProfilePolicyTest(unittest.TestCase):
    def test_primary_and_experimental_profile_policy_is_explicit(self):
        config = json.loads((ROOT / "config" / "profiles.json").read_text())
        self.assertEqual(config["default_profile"], "omega-cyan")
        primary = {item["id"] for item in config["profiles"] if item["tier"] == "primary"}
        experimental = {item["id"] for item in config["profiles"] if item["tier"] == "experimental"}
        self.assertEqual(primary, {"omega-cyan", "omega-gold", "omega-silver"})
        self.assertEqual(experimental, {"aion-cyan", "hints-core"})
        self.assertTrue(all(item["tier"] in {"primary", "supported", "experimental"} for item in config["profiles"]))


if __name__ == "__main__":
    unittest.main()
