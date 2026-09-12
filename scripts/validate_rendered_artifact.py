#!/usr/bin/env python3
import argparse, json, re, sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--html",required=True);p.add_argument("--bundle",required=True);a=p.parse_args();h=Path(a.html).read_text();b=json.loads((Path(a.bundle)/"truth-model.json").read_text());errors=[]
 for c in b["claims"]:
  for token in c.get("protected_tokens",[]):
   if token not in h: errors.append({"code":"PROTECTED_TOKEN_MISSING","detail":token})
 for needle in ("<!doctype html>","omega:theme_profile","omega:language","@media print"):
  if needle not in h: errors.append({"code":"ARTIFACT_MARKER_MISSING","detail":needle})
 if re.search(r"https?://|url\(",h): errors.append({"code":"REMOTE_DEPENDENCY","detail":"remote URL"})
 if "{{" in h: errors.append({"code":"UNRESOLVED_TEMPLATE","detail":"template marker"})
 print(json.dumps({"status":"FAIL" if errors else "PASS","errors":errors},ensure_ascii=False));return 2 if errors else 0
if __name__=="__main__":sys.exit(main())
