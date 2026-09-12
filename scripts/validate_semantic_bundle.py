#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def e(c,l,d): return {"code":c,"location":l,"detail":d}
def run(paths):
 d={k:(v if isinstance(v,dict) else json.loads(Path(v).read_text())) for k,v in paths.items()}; out=[]
 schema_names={"truth":"truth-model","reader":"reader-brief","strategy":"document-strategy","authored":"authored-content","composition":"composition-model"}
 for k in paths:
  for x in Draft202012Validator(json.loads((ROOT/"schemas"/(schema_names[k]+".schema.json")).read_text())).iter_errors(d[k]): out.append(e("SCHEMA_INVALID",k,x.message))
 if out:return out
 t,a,c=d["truth"],d["authored"],d["composition"]
 def uniq(xs,key,code,kind):
  seen=set()
  for i,x in enumerate(xs):
   if x[key] in seen:out.append(e(code,f"{kind}[{i}].{key}",x[key]))
   seen.add(x[key])
 uniq(t["sources"],"source_id","DUPLICATE_SOURCE_ID","truth.sources");uniq(t["claims"],"claim_id","DUPLICATE_CLAIM_ID","truth.claims");uniq(a["blocks"],"copy_id","DUPLICATE_COPY_ID","authored.blocks");uniq(c["sections"],"section_id","DUPLICATE_SECTION_ID","composition.sections")
 structured=[b for s in c["sections"] for b in s.get("structured_blocks",[])]
 uniq(structured,"block_id","DUPLICATE_STRUCTURED_BLOCK_ID","composition.structured_blocks")
 sources={x["source_id"] for x in t["sources"]}; claims={x["claim_id"]:x for x in t["claims"]}; copies={x["copy_id"]:x for x in a["blocks"]}; authored=set();composed=set()
 for x in t["claims"]:
  for s in x.get("source_refs",[]):
   if s not in sources:out.append(e("UNKNOWN_SOURCE_REF","truth",s))
 for i,x in enumerate(a["blocks"]):
  for r in x["claim_refs"]:
   if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"authored.blocks[{i}]",r))
   else:authored.add(r)
  if len(x.get("protected_spans",[])) != len(set(x.get("protected_spans",[]))):out.append(e("DUPLICATE_PROTECTED_SPAN",f"authored.blocks[{i}]","duplicate protected span"))
  for s in x.get("protected_spans",[]):
   if s not in x["text"]:out.append(e("PROTECTED_SPAN_MISSING_FROM_COPY",f"authored.blocks[{i}]",s))
   if not any(s in claims[r].get("protected_tokens",[]) for r in x["claim_refs"] if r in claims):out.append(e("UNAUTHORIZED_PROTECTED_SPAN",f"authored.blocks[{i}]",s))
  for p in x.get("state_projections",[]):
   if p["claim_id"] not in claims or p["claim_id"] not in x["claim_refs"]:out.append(e("INVALID_STATE_PROJECTION",f"authored.blocks[{i}].state_projections","claim linkage invalid"))
   elif p["dimension"] not in ("epistemic_state","closure_state","risk") or claims[p["claim_id"]].get(p["dimension"])!=p["value"]:out.append(e("STATE_PROJECTION_MISMATCH",f"authored.blocks[{i}].state_projections","value mismatch"))
 for i,s in enumerate(c["sections"]):
  for r in s.get("claim_refs",[]):
   if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"composition.sections[{i}].claim_refs",r))
   else:composed.add(r)
  for r in s["copy_refs"]:
   if r not in copies:out.append(e("UNKNOWN_COPY_REF",f"composition.sections[{i}]",r))
   else:composed.update(copies[r]["claim_refs"])
  composed.update(r for r in s.get("claim_refs",[]) if r in claims)
  for bi,b in enumerate(s.get("structured_blocks",[])):
   for r in b.get("claim_refs",[]):
    if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"composition.sections[{i}].structured_blocks[{bi}]",r))
    else:composed.add(r)
   for r in b.get("copy_refs",[]):
    if r not in copies:out.append(e("UNKNOWN_COPY_REF",f"composition.sections[{i}].structured_blocks[{bi}]",r))
    else:composed.update(copies[r]["claim_refs"])
   for item in b.get("items",[]):
    for r in item.get("claim_refs",[]):
     if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"composition.sections[{i}].structured_blocks[{bi}].items",r))
     else:composed.add(r)
    for r in item.get("copy_refs",[]):
     if r not in copies:out.append(e("UNKNOWN_COPY_REF",f"composition.sections[{i}].structured_blocks[{bi}].items",r))
     else:composed.update(copies[r]["claim_refs"])
   for ri,row in enumerate(b.get("rows",[])):
    for r in row.get("claim_refs",[]):
     if r not in claims:out.append(e("UNKNOWN_CLAIM_REF",f"composition.sections[{i}].structured_blocks[{bi}].rows[{ri}]",r))
     else:composed.add(r)
    for r in row.get("copy_refs",[]):
     if r not in copies:out.append(e("UNKNOWN_COPY_REF",f"composition.sections[{i}].structured_blocks[{bi}].rows[{ri}]",r))
     else:composed.update(copies[r]["claim_refs"])
 for x in t["claims"]:
  if x.get("materiality")=="material":
   if x["claim_id"] not in authored:out.append(e("MATERIAL_CLAIM_NOT_AUTHORED",x["claim_id"],"not authored"))
   if x["claim_id"] not in composed:out.append(e("MATERIAL_CLAIM_NOT_COMPOSED",x["claim_id"],"not composed"))
 return out
def main():
 p=argparse.ArgumentParser()
 for n in ("truth","reader","strategy","authored","composition"):p.add_argument("--"+n,required=True)
 a=p.parse_args();paths={"truth":a.truth,"reader":a.reader,"strategy":a.strategy,"authored":a.authored,"composition":a.composition}
 try:
  errors=run(paths)
  if any(x["code"]=="SCHEMA_INVALID" for x in errors):
   print(json.dumps({"status":"FAIL","errors":errors,"warnings":[]},ensure_ascii=False));return 2
  t=json.loads(Path(a.truth).read_text());material={x["claim_id"] for x in t.get("claims",[]) if x.get("materiality")=="material"}
 except (OSError,ValueError) as exc:
  print(json.dumps({"status":"FAIL","errors":[e("SCHEMA_INVALID","bundle",str(exc))],"warnings":[]},ensure_ascii=False));return 2
 authored=json.loads(Path(a.authored).read_text());composition=json.loads(Path(a.composition).read_text());authored_ids={r for b in authored.get("blocks",[]) for r in b.get("claim_refs",[])};composed_ids={r for s in composition.get("sections",[]) for r in s.get("claim_refs",[])}
 composed_ids.update(r for s in composition.get("sections",[]) for c in s.get("copy_refs",[]) for b in authored.get("blocks",[]) if b.get("copy_id")==c for r in b.get("claim_refs",[]))
 for s in composition.get("sections",[]):
  for b in s.get("structured_blocks",[]):
   composed_ids.update(b.get("claim_refs",[]))
   composed_ids.update(r for c in b.get("copy_refs",[]) for block in authored.get("blocks",[]) if block.get("copy_id")==c for r in block.get("claim_refs",[]))
   composed_ids.update(r for item in b.get("items",[]) for r in item.get("claim_refs",[]))
   composed_ids.update(r for row in b.get("rows",[]) for r in row.get("claim_refs",[]))
 out={"status":"FAIL" if errors else "PASS","errors":errors,"warnings":[],"coverage":{"material_claims":len(material),"authored_material_claims":len(material&authored_ids),"composed_material_claims":len(material&composed_ids)}};print(json.dumps(out,ensure_ascii=False));return 2 if errors else 0
if __name__=="__main__":sys.exit(main())
