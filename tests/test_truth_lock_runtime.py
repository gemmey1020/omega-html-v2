import copy, json, subprocess, sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_semantic_bundle import run
ROOT=Path(__file__).resolve().parents[1]; F=ROOT/"tests/fixtures/core-contracts"
def bundle():
 return {k:json.loads((F/f"{n}.json").read_text()) for k,n in {"truth":"truth-model","reader":"reader-brief","strategy":"document-strategy","authored":"authored-content","composition":"composition-model"}.items()}
class TruthLockRuntimeTest(unittest.TestCase):
 def codes(self,d): return {x["code"] for x in run(d)}
 def test_unknown_source_reference_is_rejected(self):
  d=bundle(); d["truth"]["claims"][0]["source_refs"]=["SOURCE.MISSING"]; self.assertIn("UNKNOWN_SOURCE_REF",self.codes(d))
 def test_projection_with_missing_claim_is_invalid(self):
  d=bundle(); d["authored"]["blocks"][0]["state_projections"][0]["claim_id"]="CLAIM.MISSING"; codes=self.codes(d); self.assertIn("INVALID_STATE_PROJECTION",codes); self.assertNotIn("STATE_PROJECTION_MISMATCH",codes)
 def test_projection_claim_must_be_referenced_by_copy(self):
  d=bundle(); d["truth"]["claims"].append({"claim_id":"DEMO.OTHER","meaning":"other","epistemic_state":"source_backed","closure_state":"open","risk":"low","source_refs":["SOURCE.RELEASE.BRIEF"],"materiality":"contextual"}); d["authored"]["blocks"][0]["state_projections"][0]["claim_id"]="DEMO.OTHER"; codes=self.codes(d); self.assertIn("INVALID_STATE_PROJECTION",codes)
 def test_projection_value_mismatch_is_distinct(self):
  d=bundle(); d["authored"]["blocks"][0]["state_projections"][0]["value"]="verified"; codes=self.codes(d); self.assertIn("STATE_PROJECTION_MISMATCH",codes); self.assertNotIn("INVALID_STATE_PROJECTION",codes)
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
  bad=bundle();bad["truth"]["claims"][0]["source_refs"]=["UNKNOWN"]
  with tempfile.TemporaryDirectory() as td:
   td=Path(td); paths={k:td/f"{k}.json" for k in ("truth","reader","strategy","authored","composition")}
   for k,v in bad.items(): paths[k].write_text(json.dumps(v))
   fail=[sys.executable,str(ROOT/"scripts/validate_semantic_bundle.py")]+sum((["--"+k,str(paths[k])] for k in paths),[])
   result=subprocess.run(fail,capture_output=True,text=True);self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stdout)["status"],"FAIL");self.assertIn("UNKNOWN_SOURCE_REF",result.stdout);self.assertNotIn("Traceback",result.stderr)
 def cli_args(self,paths):
  return [sys.executable,str(ROOT/"scripts/validate_semantic_bundle.py")]+sum((["--"+k,str(paths[k])] for k in paths),[])
 def test_cli_schema_invalid_bundle_returns_structured_failure(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td); paths={k:d/(k+".json") for k in ("truth","reader","strategy","authored","composition")}; data=bundle(); data["authored"]["blocks"]="oops"
   for k,v in data.items(): paths[k].write_text(json.dumps(v))
   r=subprocess.run(self.cli_args(paths),capture_output=True,text=True); payload=json.loads(r.stdout); self.assertEqual(r.returncode,2); self.assertEqual(payload["status"],"FAIL"); self.assertIn("SCHEMA_INVALID",{x["code"] for x in payload["errors"]}); self.assertNotIn("Traceback",r.stderr)
 def test_cli_semantic_invalid_bundle_returns_structured_failure(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td); paths={k:d/(k+".json") for k in ("truth","reader","strategy","authored","composition")}; data=bundle(); data["truth"]["claims"][0]["source_refs"]=["SOURCE.MISSING"]
   for k,v in data.items(): paths[k].write_text(json.dumps(v))
   r=subprocess.run(self.cli_args(paths),capture_output=True,text=True); payload=json.loads(r.stdout); self.assertEqual(r.returncode,2); self.assertEqual(payload["status"],"FAIL"); self.assertIn("UNKNOWN_SOURCE_REF",{x["code"] for x in payload["errors"]}); self.assertNotIn("Traceback",r.stderr)
 def test_cli_valid_bundle_reports_coverage(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td); paths={k:d/(k+".json") for k in ("truth","reader","strategy","authored","composition")}; data=bundle()
   for k,v in data.items(): paths[k].write_text(json.dumps(v))
   r=subprocess.run(self.cli_args(paths),capture_output=True,text=True); payload=json.loads(r.stdout); self.assertEqual(r.returncode,0); self.assertEqual(payload["status"],"PASS"); self.assertEqual(payload["errors"],[]); self.assertEqual(payload["coverage"],{"material_claims":1,"authored_material_claims":1,"composed_material_claims":1})
if __name__=="__main__":unittest.main()
