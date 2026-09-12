import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Wave5ArtifactTest(unittest.TestCase):
 def test_three_bundles_and_outputs_exist(self):
  for name in ("ahs","proposal","technical"):
   self.assertTrue((ROOT/"evals/bundles"/name/"truth-model.json").is_file())
   self.assertTrue((ROOT/"evals/rendered"/(name+"-v2.html")).is_file())
 def test_ahs_has_24_material_requirements_and_supporting_facts(self):
  d=json.loads((ROOT/"evals/bundles/ahs/truth-model.json").read_text());requirements=[x for x in d["claims"] if x["claim_id"].startswith("AHS.REQUIREMENT.")];self.assertEqual(len(requirements),24);self.assertEqual(sum(x.get("materiality")=="material" for x in d["claims"]),24);self.assertGreater(len(d["claims"]),24)
 def test_rendered_artifacts_are_standalone(self):
  for name in ("ahs","proposal","technical"):
   h=(ROOT/"evals/rendered"/(name+"-v2.html")).read_text();self.assertIn("<!doctype html>",h);self.assertIn("@media print",h);self.assertNotIn("https://",h)
if __name__=="__main__":unittest.main()
