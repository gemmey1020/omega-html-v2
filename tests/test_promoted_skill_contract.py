import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
OPENAI = ROOT / "agents" / "openai.yaml"
OUTPUT_CONTRACT = ROOT / "references" / "output-contract.md"


class PromotedSkillContractTest(unittest.TestCase):
    def test_skill_is_written_as_an_installed_production_surface(self):
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        description = re.search(r"^description:\s*(.+)$", frontmatter, re.M).group(1)
        self.assertTrue(description.startswith("Use when "))
        lowered = text.lower()
        for stale in ("not the installed", "unpromoted", "keep the candidate isolated", "explicit promotion decision"):
            self.assertNotIn(stale, lowered)

    def test_natural_text_and_primary_profile_defaults_are_explicit(self):
        skill = SKILL.read_text(encoding="utf-8")
        metadata = OPENAI.read_text(encoding="utf-8")
        self.assertIn("ordinary user text as the payload", skill)
        self.assertIn("ask which primary profile", skill)
        self.assertIn("ask which profile", metadata)
        self.assertIn("Gold", metadata)
        self.assertIn("Silver", metadata)
        self.assertIn("A profile is required", OUTPUT_CONTRACT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
