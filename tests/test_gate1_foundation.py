from pathlib import Path
import hashlib
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
V1 = Path("/home/jemy/.codex/skills/omega-html")
V1_SNAPSHOT = Path("/home/jemy/.codex/skill-backups/omega-html-v1-20260914T141729Z")
MANIFEST = SKILL_ROOT / "manifests" / "v1-manifest.tsv"


class Gate1FoundationTest(unittest.TestCase):
  def test_v1_manifest_exists(self):
    self.assertTrue(MANIFEST.is_file())
    self.assertIn("SKILL.md\t", MANIFEST.read_text())


  def test_candidate_does_not_point_output_at_installed_v1(self):
    self.assertNotEqual(SKILL_ROOT, V1)
    self.assertNotIn(V1, SKILL_ROOT.parents)
    self.assertFalse((SKILL_ROOT / "output").exists())


  def test_preserved_v1_snapshot_matches_frozen_manifest(self):
    for line in MANIFEST.read_text().splitlines()[1:]:
      if not line or line.startswith("#"):
        continue
      relative, expected, _size = line.split("\t")
      actual = hashlib.sha256((V1_SNAPSHOT / relative).read_bytes()).hexdigest()
      self.assertEqual(actual, expected, relative)

  def test_live_v1_is_a_deprecated_router_to_v2(self):
    skill = (V1 / "SKILL.md").read_text(encoding="utf-8").lower()
    metadata = (V1 / "agents" / "openai.yaml").read_text(encoding="utf-8").lower()
    self.assertIn("deprecated", skill)
    self.assertIn("omega-html-v2", skill)
    self.assertIn("ask", skill)
    self.assertIn("profile", skill)
    self.assertIn("omega-html-v2", metadata)
