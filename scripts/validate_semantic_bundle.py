#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def e(c,l,d): return {"code":c,"location":l,"detail":d}
def run(paths):
 d={k:json.loads(Path(v).read_text()) for k,v in paths.items()}; out=[]
 for k in paths:
  for x in Draft202012Validator(json.loads((ROOT/"schemas"/(k+".schema.json")).read_text())).iter_errors(d[k]): out.append(e("SCHEMA_INVALID",k,x.message))
 if out:return out
 t,a,c=d["truth-model"],d["authored-content"],d["composition-model"]
 def uniq(xs,key,code):
  seen=set()
  for i,x in enumerate(xs):
   if x[key] in seen:out.append(e(code,f"{key}[{i}]",x[key]))
   seen.add(x[key])
 uniq(t["sources"],"source_id","DUPLICATE_SOURCE_ID");uniq(t["claims"],"claim_id","DUPLICATE_CLAIM_ID");uniq(a["blocks"],"copy_id","DUPLICATE_COPY_ID");uniq(c["sections"],"section_id","DUPLICATE_SECTION_ID")
 sources={x["source_id"] for x in t["sources"]}; claims={x["claim_id"]:x for x in t["claims"]}; copies={x["copy_id"]:x for x in a["blocks"]}; authored=set();composed=set()
 for x in t["claims"]:
  for s in x.get("source_refs",[]):
   if s not in sources:out.append(e("UNKNOWN_SOURCE_REF","truth",s))
 for i,x in enumerate(a["blocks"]):
  for r in x["claim_refs"]:
   if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"authored.blocks[{i}]",r))
   else:authored.add(r)
  for s in x.get("protected_spans",[]):
   if s not in x["text"]:out.append(e("PROTECTED_SPAN_MISSING_FROM_COPY",f"authored.blocks[{i}]",s))
   if not any(s in claims[r].get("protected_tokens",[]) for r in x["claim_refs"] if r in claims):out.append(e("UNAUTHORIZED_PROTECTED_SPAN",f"authored.blocks[{i}]",s))
  for p in x.get("state_projections",[]):
   if p["claim_id"] not in claims or p["claim_id"] not in x["claim_refs"] or p["dimension"] not in ("epistemic_state","closure_state","risk") or claims[p["claim_id"]].get(p["dimension"])!=p["value"]:out.append(e("STATE_PROJECTION_MISMATCH",f"authored.blocks[{i}]",str(p)))
 for i,s in enumerate(c["sections"]):
  for r in s["copy_refs"]:
   if r not in copies:out.append(e("UNKNOWN_COPY_REF",f"composition.sections[{i}]",r))
   else:composed.update(copies[r]["claim_refs"])
  composed.update(s.get("claim_refs",[]))
 for x in t["claims"]:
  if x.get("materiality")=="material":
   if x["claim_id"] not in authored:out.append(e("MATERIAL_CLAIM_NOT_AUTHORED",x["claim_id"],"not authored"))
   if x["claim_id"] not in composed:out.append(e("MATERIAL_CLAIM_NOT_COMPOSED",x["claim_id"],"not composed"))
 return out
def main():
 p=argparse.ArgumentParser()
 for n in ("truth","reader","strategy","authored","composition"):p.add_argument("--"+n,required=True)
 a=p.parse_args();paths={"truth-model":a.truth,"reader-brief":a.reader,"document-strategy":a.strategy,"authored-content":a.authored,"composition-model":a.composition};errors=run(paths);print(json.dumps({"status":"FAIL" if errors else "PASS","errors":errors,"warnings":[]},ensure_ascii=False));return 2 if errors else 0
if __name__=="__main__":sys.exit(main())
