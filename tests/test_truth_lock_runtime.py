import copy, json, subprocess, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_semantic_bundle import run
ROOT=Path(__file__).resolve().parents[1]; F=ROOT/"tests/fixtures/core-contracts"
def bundle():
 return {k:json.loads((F/f"{n}.json").read_text()) for k,n in {"truth":"truth-model","reader":"reader-brief","strategy":"document-strategy","authored":"authored-content","composition":"composition-model"}.items()}
class TruthLockRuntimeTest(unittest.TestCase):
 def codes(self,d): return {x["code"] for x in run(d)}
 def test_good_bundle(self): self.assertEqual(self.codes(bundle()),set())
 def test_source_and_claim_duplicates(self):
  d=bundle();d["truth"]["sources"].append(copy.deepcopy(d["truth"]["sources"][0]));self.assertIn("DUPLICATE_SOURCE_ID",self.codes(d))
  d=bundle();d["truth"]["claims"].append(copy.deepcopy(d["truth"]["claims"][0]));self.assertIn("DUPLICATE_CLAIM_ID",self.codes(d))
 def test_reference_failures(self):
  for layer,key,code in [("authored","claim_refs","UNKNOWN_CLAIM_REF"),("composition","copy_refs","UNKNOWN_COPY_REF")]:
   d=bundle();d[layer]["blocks" if layer=="authored" else "sections"][0][key]=["UNKNOWN"];self.assertIn(code,self.codes(d))
 def test_composition_claim_ref_failure(self):
  d=bundle();d["composition"]["sections"][0]["claim_refs"]=["CLAIM.UNKNOWN"];self.assertIn("UNKNOWN_CLAIM_REF",self.codes(d))
 def test_protected_failures(self):
  d=bundle();d["authored"]["blocks"][0]["protected_spans"]=["missing"];self.assertIn("PROTECTED_SPAN_MISSING_FROM_COPY",self.codes(d))
  d=bundle();d["authored"]["blocks"][0]["protected_spans"]=["unauthorized"];self.assertIn("UNAUTHORIZED_PROTECTED_SPAN",self.codes(d))
  d=bundle();d["authored"]["blocks"][0]["protected_spans"]=["2026-10-01","2026-10-01"];self.assertIn("DUPLICATE_PROTECTED_SPAN",self.codes(d))
 def test_material_coverage(self):
  d=bundle();d["authored"]["blocks"][0]["claim_refs"]=[];self.assertIn("MATERIAL_CLAIM_NOT_AUTHORED",self.codes(d))
  d=bundle();d["composition"]["sections"][0]["copy_refs"]=[];d["composition"]["sections"][0]["claim_refs"]=[];self.assertIn("MATERIAL_CLAIM_NOT_COMPOSED",self.codes(d))
 def test_state_mismatch_and_copy_duplicate(self):
  d=bundle();d["authored"]["blocks"][0]["state_projections"][0]["value"]="verified";self.assertIn("STATE_PROJECTION_MISMATCH",self.codes(d))
  d=bundle();d["authored"]["blocks"].append(copy.deepcopy(d["authored"]["blocks"][0]));self.assertIn("DUPLICATE_COPY_ID",self.codes(d))
  d=bundle();d["composition"]["sections"].append(copy.deepcopy(d["composition"]["sections"][0]));self.assertIn("DUPLICATE_SECTION_ID",self.codes(d))
 def test_cli_pass_and_fail(self):
  args=[sys.executable,str(ROOT/"scripts/validate_semantic_bundle.py")]
  for key in ("truth","reader","strategy","authored","composition"): args += ["--"+key,str(F/({"truth":"truth-model","reader":"reader-brief","strategy":"document-strategy","authored":"authored-content","composition":"composition-model"}[key]+".json"))]
  ok=subprocess.run(args,capture_output=True,text=True);self.assertEqual(ok.returncode,0);self.assertEqual(json.loads(ok.stdout)["status"],"PASS");self.assertIn("coverage",ok.stdout)
  bad=subprocess.run(args[:-2]+[str(F/"missing.json")],capture_output=True,text=True);self.assertNotEqual(bad.returncode,0);self.assertNotIn("Traceback",bad.stderr)
if __name__=="__main__":unittest.main()
