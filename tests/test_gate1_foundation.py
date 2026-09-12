from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "skills" / "omega-html-v2-candidate"
V1 = Path("/home/jemy/.codex/skills/omega-html")
MANIFEST = CANDIDATE / "manifests" / "v1-manifest.tsv"


class Gate1FoundationTest(unittest.TestCase):
  def test_v1_manifest_exists(self):
    self.assertTrue(MANIFEST.is_file())
    self.assertIn("SKILL.md\t", MANIFEST.read_text())


  def test_candidate_does_not_point_output_at_installed_v1(self):
    self.assertFalse(str(CANDIDATE).startswith(str(V1)))
    self.assertFalse((CANDIDATE / "output").exists())


  def test_live_v1_matches_frozen_manifest(self):
    for line in MANIFEST.read_text().splitlines()[1:]:
      if not line or line.startswith("#"):
        continue
      relative, expected, _size = line.split("\t")
      actual = hashlib.sha256((V1 / relative).read_bytes()).hexdigest()
      self.assertEqual(actual, expected, relative)
