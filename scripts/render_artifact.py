#!/usr/bin/env python3
import argparse, html, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
THEMES={
 "omega-editorial":{"bg":"#f4f0e8","surface":"#fffdf8","ink":"#17201f","muted":"#586261","accent":"#9b5f35","line":"#d8cec0","display":"Georgia, 'Noto Serif Arabic', serif","body":"'Noto Sans Arabic', Arial, sans-serif"},
 "omega-minimal":{"bg":"#f7f8f7","surface":"#ffffff","ink":"#182322","muted":"#5c6866","accent":"#147d72","line":"#d9e2df","display":"'Noto Sans Arabic', Arial, sans-serif","body":"'Noto Sans Arabic', Arial, sans-serif"},
 "omega-hud":{"bg":"#080d11","surface":"#111a20","ink":"#edf7f3","muted":"#a9bbb7","accent":"#55e6c3","line":"#29463f","display":"Georgia, 'Noto Serif Arabic', serif","body":"'Noto Sans Arabic', Arial, sans-serif"},
 "aion":{"bg":"#05090d","surface":"#101a20","ink":"#eefbff","muted":"#a3b9c0","accent":"#39e6ff","line":"#244451","display":"'Segoe UI', Arial, sans-serif","body":"'Noto Sans Arabic', Arial, sans-serif"}}
def load_bundle(d): return {k:json.loads((Path(d)/f"{n}.json").read_text()) for k,n in {"truth":"truth-model","reader":"reader-brief","strategy":"document-strategy","authored":"authored-content","composition":"composition-model"}.items()}
def truthlock(d):
 p=ROOT/"scripts"/"validate_semantic_bundle.py"; args=d
 # imported runtime accepts dictionaries; preserve one source of truth.
 sys.path.insert(0,str(ROOT)); from scripts.validate_semantic_bundle import run
 return run(args)
def render(d, profile):
 t=d["truth"]; a=d["authored"]; c=d["composition"]; r=d["reader"]; th=THEMES[profile]
 blocks={x["copy_id"]:x for x in a["blocks"]}; claims={x["claim_id"]:x for x in t["claims"]}
 def text(x): return html.escape(str(x))
 sections=[]
 for s in c["sections"]:
  body=[]
  for ref in s.get("copy_refs",[]):
   b=blocks.get(ref)
   if not b: continue
   role=b.get("role","paragraph"); tag="h3" if role in ("headline","subheadline","table_heading") else "p"
   cls="copy copy--"+text(role); body.append(f"<{tag} class='{cls}'>{text(b['text'])}</{tag}>")
  sections.append(f"<section class='section section--{text(s['presentation_intent'])}'><div class='section-kicker'>{text(s['presentation_intent'].replace('_',' '))}</div><h2>{text(s['purpose'])}</h2>{''.join(body)}</section>")
 hero=next((b for b in a["blocks"] if b.get("role")=="headline"),None)
 title=hero["text"] if hero else r.get("document_intent","Omega HTML")
 lang=r.get("language",{}).get("primary","en"); direction=r.get("language",{}).get("direction","ltr")
 source_count=len(t.get("sources",[])); protected=sum(len(x.get("protected_tokens",[])) for x in t.get("claims",[]))
 css=f":root{{--bg:{th['bg']};--surface:{th['surface']};--ink:{th['ink']};--muted:{th['muted']};--accent:{th['accent']};--line:{th['line']};--display:{th['display']};--body:{th['body']}}}"
 return f'''<!doctype html><html lang="{text(lang)}" dir="{text(direction)}" data-surface-profile="{profile}"><head><meta charset="utf-8"><meta name="omega:surface" content="document"><meta name="omega:theme_profile" content="{profile}"><meta name="omega:language" content="{lang}"><meta name="omega:direction" content="{direction}"><meta name="omega:source_count" content="{source_count}"><meta name="omega:protected_token_count" content="{protected}"><title>{text(title)}</title><style>{css}*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);line-height:1.8}}.page{{max-width:1100px;margin:auto;padding:28px clamp(18px,4vw,64px)}}header{{padding:clamp(38px,8vw,100px) 0 56px;border-bottom:1px solid var(--line)}}.eyebrow,.section-kicker{{color:var(--accent);font:700 11px/1.3 var(--body);letter-spacing:.12em;text-transform:uppercase}}h1,h2,h3{{font-family:var(--display);line-height:1.18}}h1{{font-size:clamp(2.4rem,6vw,5.8rem);max-width:900px;margin:18px 0}}.lede{{max-width:760px;color:var(--muted);font-size:1.12rem}}main{{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,.34fr);gap:clamp(28px,6vw,80px);padding:48px 0}}.section{{padding:0 0 42px;margin:0 0 42px;border-bottom:1px solid var(--line)}}.section h2{{font-size:clamp(1.35rem,2.5vw,2rem);margin:10px 0 20px}}.section--technical_block,.section--technical_annex{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.9rem;overflow-wrap:anywhere}}.copy--label,.copy--status{{display:inline-block;color:var(--accent);font-weight:700;margin-inline-end:1em}}aside{{background:var(--surface);border-inline-start:3px solid var(--accent);padding:20px;height:max-content}}footer{{border-top:1px solid var(--line);padding:24px 0;color:var(--muted);font-size:.82rem}}code,.ltr{{direction:ltr;unicode-bidi:plaintext;overflow-wrap:anywhere}}@media(max-width:760px){{.page{{padding:18px}}main{{display:block}}aside{{margin-top:8px}}h1{{font-size:clamp(2.2rem,12vw,3.8rem)}}}}@media print{{@page{{size:A4;margin:16mm}}html,body{{background:#fff;color:#111}}.page{{max-width:none;padding:0}}header{{padding:18mm 0 12mm}}aside{{background:#fff;break-inside:avoid}}.section{{break-inside:avoid-page}}.section--technical_annex{{break-before:page}}footer{{margin-top:12mm}}}}</style></head><body><div class="page"><header><div class="eyebrow">Ω OMEGA HTML · {text(profile)}</div><h1>{text(title)}</h1><p class="lede">{text(next((b['text'] for b in a['blocks'] if b.get('role')=='subheadline'),''))}</p></header><main><div>{''.join(sections)}</div><aside><strong>{text(r.get('audience','reader'))}</strong><p>{text(r.get('primary_question',''))}</p></aside></main><footer>Truth-first artifact · {source_count} sources · {protected} protected tokens · render profile {text(profile)}</footer></div></body></html>'''
def main():
 p=argparse.ArgumentParser();p.add_argument("--bundle",required=True);p.add_argument("--output",required=True);p.add_argument("--surface-profile",choices=THEMES,default="omega-editorial");a=p.parse_args();d=load_bundle(a.bundle);errors=truthlock(d)
 if errors: print(json.dumps({"status":"REJECT","errors":errors},ensure_ascii=False)); return 2
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(d,a.surface_profile),encoding="utf-8");print(json.dumps({"status":"PASS","path":str(out),"surface_profile":a.surface_profile},ensure_ascii=False));return 0
if __name__=="__main__":sys.exit(main())
