import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class WritingDependencyTest(unittest.TestCase):
 def test_manifest_and_selected_pins(self):
  d=json.loads((ROOT/"manifests/writing-dependencies.json").read_text()); selected=[x for x in d["evaluated"] if x["selected"]]
  self.assertEqual(sum(x["role"].startswith("primary") for x in selected),1); self.assertEqual(sum(x["role"].startswith("UX") for x in selected),1); self.assertEqual(sum(x["role"].startswith("final") for x in selected),1)
  for x in selected:
   self.assertRegex(x["resolved_commit"],r"^[0-9a-f]{40}$"); self.assertTrue((ROOT/"third_party/writing"/({"primary human-first authoring":"humanize-writing","UX writing for compact copy roles":"ux-writing-skill","final conservative humanity":"humanizer"}[x["role"]])/"LICENSE").is_file())
 def test_routing_boundaries(self):
  d=json.loads((ROOT/"config/authoring-routing.json").read_text());self.assertTrue(d["truth_lock"]["before_authoring"]);self.assertTrue(d["truth_lock"]["after_authoring"]);self.assertEqual(d["routes"]["technical_text"],[]);self.assertTrue(d["voice"]["requires_reader_brief_and_evidence"])
 def test_no_global_install_and_snapshot_hashes(self):
  self.assertFalse((Path.home()/".codex/skills/humanize-writing").exists())
  for dep in ("humanize-writing","ux-writing-skill","humanizer"):
   self.assertTrue((ROOT/"third_party/writing"/dep/"SKILL.md").is_file())
if __name__=="__main__":unittest.main()
