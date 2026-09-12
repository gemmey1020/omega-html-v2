#!/usr/bin/env python3
"""Render a validated Omega semantic bundle as one standalone HTML artifact."""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "omega-editorial": {"bg": "#f4f0e8", "surface": "#fffdf8", "ink": "#17201f", "muted": "#586261", "accent": "#9b5f35", "line": "#d8cec0", "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif"},
    "omega-minimal": {"bg": "#f5f8f6", "surface": "#ffffff", "ink": "#182322", "muted": "#5c6866", "accent": "#147d72", "line": "#d9e2df", "display": "'Noto Sans Arabic', Arial, sans-serif", "body": "'Noto Sans Arabic', Arial, sans-serif"},
    "omega-hud": {"bg": "#081015", "surface": "#101b20", "ink": "#edf7f3", "muted": "#a9bbb7", "accent": "#55e6c3", "line": "#29463f", "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif"},
    "aion": {"bg": "#05090d", "surface": "#101a20", "ink": "#eefbff", "muted": "#a3b9c0", "accent": "#39e6ff", "line": "#244451", "display": "'Segoe UI', Arial, sans-serif", "body": "'Noto Sans Arabic', Arial, sans-serif"},
}
VISIBLE_INTENTS = {
    "ar": {"verdict": "الحكم الحالي", "narrative": "السياق", "key_fact": "حقائق أساسية", "comparison": "مقارنة", "evidence_matrix": "مصفوفة الأدلة", "risk_register": "المخاطر المفتوحة", "sequence": "تسلسل الإغلاق", "checklist": "خطوات المتابعة", "table": "جدول الحالة", "callout": "تنبيه", "technical_block": "تفصيل تقني", "technical_annex": "الملحق التقني", "source_ledger": "سجل المصادر"},
    "en": {"verdict": "Current decision", "narrative": "Context", "key_fact": "Key facts", "comparison": "Comparison", "evidence_matrix": "Evidence matrix", "risk_register": "Open risks", "sequence": "Closure sequence", "checklist": "Next steps", "table": "Status table", "callout": "Note", "technical_block": "Technical detail", "technical_annex": "Technical annex", "source_ledger": "Source ledger"},
}
DOC_LABELS = {"ar": {"audit_report": "مراجعة حقيقة تشغيلية", "proposal": "مقترح قرار", "technical": "تقرير تقني"}, "en": {"audit_report": "Operational truth review", "proposal": "Decision proposal", "technical": "Technical report"}}


def load_bundle(directory):
    directory = Path(directory)
    names = {"truth": "truth-model", "reader": "reader-brief", "strategy": "document-strategy", "authored": "authored-content", "composition": "composition-model"}
    return {key: json.loads((directory / f"{filename}.json").read_text(encoding="utf-8")) for key, filename in names.items()}


def truthlock(bundle):
    sys.path.insert(0, str(ROOT))
    from scripts.validate_semantic_bundle import run
    return run(bundle)


def esc(value):
    return html.escape(str(value), quote=True)


def refs_attrs(claim_refs=None, copy_refs=None):
    attrs = []
    if claim_refs:
        attrs.append(f'data-claim-id="{esc(" ".join(claim_refs))}"')
    if copy_refs:
        attrs.append(f'data-copy-ref="{esc(" ".join(copy_refs))}"')
    return " ".join(attrs)


def render_copy(block, intent="narrative"):
    role = block.get("role", "paragraph")
    attrs = f'data-copy-id="{esc(block["copy_id"])}"'
    linked = refs_attrs(block.get("claim_refs"), [block["copy_id"]])
    if linked:
        attrs += " " + linked
    classes = f'copy copy--{esc(role)} intent--{esc(intent)}'
    text = esc(block.get("text", ""))
    trace = "".join(f'<span class="trace-marker" data-claim-id="{esc(ref)}" aria-hidden="true"></span>' for ref in block.get("claim_refs", []))
    if role == "headline":
        tag = "h1"
    elif role in {"subheadline", "section_heading", "table_heading"}:
        tag = "h3"
    elif role in {"label", "status"}:
        tag = "span"
        if role == "status":
            classes += " status-pill"
    elif role == "callout":
        tag = "div"
        classes += " callout"
    elif role == "technical_text":
        return f'<pre class="technical-copy" {attrs}>{trace}<code dir="ltr">{text}</code></pre>'
    else:
        tag = "p"
    return f'<{tag} class="{classes}" {attrs}>{trace}{text}</{tag}>'


def structured_attrs(block):
    linked = refs_attrs(block.get("claim_refs"), block.get("copy_refs"))
    return f'data-structured-id="{esc(block["block_id"])}"' + (f" {linked}" if linked else "")


def render_structured(block):
    kind = block["type"]
    title = f'<h3 class="structured-title">{esc(block["title"])}</h3>' if block.get("title") else ""
    attrs = structured_attrs(block)
    if kind == "fact_list":
        rows = []
        for item in block.get("items", []):
            detail = f'<small>{esc(item["detail"])}</small>' if item.get("detail") else ""
            rows.append(f'<div class="fact" {refs_attrs(item.get("claim_refs"), item.get("copy_refs"))}><dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}{detail}</dd></div>')
        return f'<dl class="structured structured--facts" {attrs}>{title}{"".join(rows)}</dl>'
    if kind in {"table", "comparison"}:
        head = "".join(f'<th scope="col">{esc(column)}</th>' for column in block.get("columns", []))
        rows = []
        for row in block.get("rows", []):
            cells = "".join(f"<td>{esc(cell)}</td>" for cell in row.get("cells", []))
            rows.append(f'<tr {refs_attrs(row.get("claim_refs"), row.get("copy_refs"))}>{cells}</tr>')
        return f'<div class="structured structured--{kind}" {attrs}>{title}<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>'
    if kind in {"sequence", "checklist"}:
        items = []
        for item in block.get("items", []):
            detail = f'<span>{esc(item["detail"])}</span>' if item.get("detail") else ""
            items.append(f'<li {refs_attrs(item.get("claim_refs"), item.get("copy_refs"))}><strong>{esc(item["label"])}</strong>{detail}</li>')
        tag = "ol" if kind == "sequence" else "ul"
        return f'<div class="structured structured--{kind}" {attrs}>{title}<{tag}>{"".join(items)}</{tag}></div>'
    if kind == "risk_register":
        items = []
        for item in block.get("items", []):
            detail = f'<p>{esc(item["detail"])}</p>' if item.get("detail") else ""
            items.append(f'<article class="risk" {refs_attrs(item.get("claim_refs"), item.get("copy_refs"))}><strong>{esc(item["label"])}</strong><span>{esc(item["value"])}</span>{detail}</article>')
        return f'<div class="structured structured--risk" {attrs}>{title}{"".join(items)}</div>'
    if kind == "code":
        return f'<div class="structured structured--code" {attrs}>{title}<pre><code dir="ltr">{esc(block.get("code", ""))}</code></pre></div>'
    if kind == "source_ledger":
        items = "".join(f'<li {refs_attrs(item.get("claim_refs"), item.get("copy_refs"))}><strong>{esc(item["label"])}</strong><span>{esc(item["value"])}</span></li>' for item in block.get("items", []))
        return f'<div class="structured structured--ledger" {attrs}>{title}<ol>{items}</ol></div>'
    if kind == "callout":
        return f'<aside class="structured structured--callout" {attrs}>{title}<p>{esc(block.get("code", ""))}</p></aside>'
    return ""


def render(bundle, profile=None):
    truth, authored, composition, reader = bundle["truth"], bundle["authored"], bundle["composition"], bundle["reader"]
    profile = profile or reader.get("surface_profile", "omega-editorial")
    theme = THEMES[profile]
    lang = reader.get("language", {}).get("primary", "en")
    direction = reader.get("language", {}).get("direction", "ltr")
    intent = reader.get("document_intent", "report")
    labels = VISIBLE_INTENTS["ar" if lang == "ar" else "en"]
    blocks = {block["copy_id"]: block for block in authored["blocks"]}
    headline = next((block for block in authored["blocks"] if block.get("role") == "headline"), None)
    subheadline = next((block for block in authored["blocks"] if block.get("role") == "subheadline"), None)
    title = headline.get("text", "Omega document") if headline else DOC_LABELS["en"].get(intent, "Omega document")
    hero_attrs = f'data-copy-id="{esc(headline["copy_id"])}" {refs_attrs(headline.get("claim_refs"), [headline["copy_id"]])}' if headline else ""
    hero_trace = "".join(f'<span class="trace-marker" data-claim-id="{esc(ref)}" aria-hidden="true"></span>' for ref in (headline or {}).get("claim_refs", []))
    sub_attrs = f'data-copy-id="{esc(subheadline["copy_id"])}" {refs_attrs(subheadline.get("claim_refs"), [subheadline["copy_id"]])}' if subheadline else ""
    sub_trace = "".join(f'<span class="trace-marker" data-claim-id="{esc(ref)}" aria-hidden="true"></span>' for ref in (subheadline or {}).get("claim_refs", []))
    css = f'''\n:root{{--bg:{theme["bg"]};--surface:{theme["surface"]};--ink:{theme["ink"]};--muted:{theme["muted"]};--accent:{theme["accent"]};--line:{theme["line"]};--display:{theme["display"]};--body:{theme["body"]}}}\n*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);line-height:1.68}}.page{{max-width:1180px;margin:auto;padding:28px clamp(20px,5vw,76px)}}header{{padding:clamp(30px,5vw,64px) 0 34px;border-bottom:1px solid var(--line)}}.masthead{{display:flex;justify-content:space-between;gap:24px;align-items:baseline;color:var(--muted);font-size:.75rem;letter-spacing:.08em}}.eyebrow,.section-kicker{{color:var(--accent);font-size:.76rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{font-family:var(--display);line-height:1.2}}h1{{font-size:clamp(2.35rem,5vw,4.25rem);max-width:17ch;margin:18px 0 14px;letter-spacing:-.03em}}.lede{{max-width:62ch;color:var(--muted);font-size:1.04rem;margin:0}}main{{display:block;padding:40px 0 12px}}main.has-rail{{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,270px);gap:clamp(34px,6vw,78px)}}.content{{min-width:0}}.section{{padding:0 0 38px;margin:0 0 38px;border-bottom:1px solid var(--line)}}.section:last-child{{border-bottom:0}}.section h2{{font-size:clamp(1.45rem,2.5vw,2.15rem);margin:10px 0 20px;max-width:30ch}}.section-kicker{{margin-bottom:8px}}.copy{{max-width:68ch;margin:0 0 14px}}.copy--headline{{max-width:none}}.copy--label{{display:block;color:var(--muted);font-size:.79rem;font-weight:700;letter-spacing:.04em}}.status-pill{{display:inline-block;border:1px solid var(--accent);border-radius:999px;padding:2px 10px;color:var(--accent);font-size:.78rem;font-weight:700}}.callout,.structured--callout{{border-inline-start:3px solid var(--accent);background:color-mix(in srgb,var(--surface) 88%,var(--accent));padding:16px 18px;margin:20px 0}}.structured-title{{font-size:1rem;margin:0 0 14px}}.structured--facts{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin:22px 0}}.fact{{background:var(--surface);padding:15px 17px}}.fact dt{{color:var(--muted);font-size:.78rem;margin-bottom:5px}}.fact dd{{margin:0;font-size:1.03rem;font-weight:700}}.fact small{{display:block;color:var(--muted);font-size:.78rem;font-weight:400;margin-top:4px}}.table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:var(--surface);font-size:.91rem}}th,td{{padding:11px 13px;border-bottom:1px solid var(--line);text-align:start;vertical-align:top}}th{{color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.05em}}.structured--comparison table{{border-inline-start:3px solid var(--accent)}}.structured--risk{{display:grid;gap:10px}}.risk{{display:grid;grid-template-columns:minmax(130px,.35fr) minmax(100px,.25fr) minmax(0,1fr);gap:14px;align-items:start;padding:13px 0;border-bottom:1px solid var(--line)}}.risk span{{color:var(--accent);font-weight:700;font-size:.83rem}}.risk p{{margin:0;color:var(--muted)}}.structured--sequence ol,.structured--checklist ul,.structured--ledger ol{{padding:0;margin:0;list-style:none;counter-reset:item}}.structured--sequence li,.structured--checklist li{{display:grid;grid-template-columns:32px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}}.structured--sequence li::before{{counter-increment:item;content:counter(item);color:var(--accent);font-weight:700}}.structured--checklist li::before{{content:"□";color:var(--accent);font-size:1.2rem}}.structured--sequence li span,.structured--checklist li span{{grid-column:2;color:var(--muted)}}.structured--code,.technical-copy{{background:var(--surface);border:1px solid var(--line);padding:18px;overflow:auto}}pre{{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:.86rem/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;direction:ltr;text-align:left}}.structured--ledger li{{display:grid;grid-template-columns:minmax(140px,.35fr) 1fr;gap:14px;padding:10px 0;border-bottom:1px solid var(--line)}}.structured--ledger span{{color:var(--muted)}}aside.rail{{align-self:start;background:var(--surface);border-top:3px solid var(--accent);padding:18px;position:sticky;top:18px}}.rail h2{{font-size:1rem;margin:0 0 10px}}.rail p{{color:var(--muted);font-size:.9rem;margin:0}}footer{{border-top:1px solid var(--line);padding:18px 0;color:var(--muted);font-size:.78rem}}.ltr{{direction:ltr;unicode-bidi:plaintext;overflow-wrap:anywhere}}[dir="rtl"] .technical-copy,[dir="rtl"] .structured--code{{direction:ltr;text-align:left}}@media(max-width:820px){{.page{{padding:20px}}main.has-rail{{display:block}}aside.rail{{position:static;margin:0 0 32px}}h1{{font-size:clamp(2.2rem,11vw,3.5rem)}}.structured--facts{{grid-template-columns:1fr}}.risk{{grid-template-columns:1fr;gap:4px}}.masthead{{display:block}}.masthead .document-label{{margin-top:6px}}}}@media print{{@page{{size:A4;margin:15mm}}html,body{{background:#fff;color:#111}}.page{{max-width:none;padding:0}}header{{padding:8mm 0 10mm}}main,main.has-rail{{display:block;padding-top:8mm}}aside.rail{{position:static;break-inside:avoid;background:#fff;border:1px solid #999;margin:0 0 8mm}}.section{{break-inside:avoid-page;margin-bottom:8mm;padding-bottom:8mm}}.structured--technical_annex{{break-before:page}}table{{font-size:9pt}}.table-scroll{{overflow:visible}}footer{{margin-top:8mm}}}}'''
    # The closing f-string escape at the end of the print rule is normalized
    # here so the artifact never carries a template-looking `}}` marker.
    css = css.replace("}}", "}")
    css = css.replace("@media print{", "@media print{html,body{--surface:#fff;--line:#ccc;--muted:#555;--accent:#333}")
    sections = []
    for section in composition["sections"]:
        section_intent = section["presentation_intent"]
        section_label = labels.get(section_intent, section_intent)
        copy_html = "".join(render_copy(blocks[ref], section_intent) for ref in section.get("copy_refs", []) if ref in blocks and blocks[ref].get("role") not in {"headline", "subheadline"})
        structured_html = "".join(render_structured(block) for block in section.get("structured_blocks", []))
        attrs = f'data-section-id="{esc(section["section_id"])}" data-presentation-intent="{esc(section_intent)}"'
        sections.append(f'<section class="section section--{esc(section_intent)}" {attrs}><div class="section-kicker">{esc(section_label)}</div><h2>{esc(section["purpose"])}</h2>{copy_html}{structured_html}</section>')
    rail = reader.get("summary_rail", {})
    rail_html = f'<aside class="rail"><h2>{esc(rail.get("title", ""))}</h2><p>{esc(rail.get("body", ""))}</p></aside>' if rail.get("enabled") else ""
    main_class = "main has-rail" if rail.get("enabled") else "main"
    footer = "مستند مستقل؛ محتواه قابل للتدقيق من خلال سجل المصادر." if lang == "ar" else "Standalone document; content is traceable through the source ledger."
    return f'''<!doctype html><html lang="{esc(lang)}" dir="{esc(direction)}" data-surface-profile="{esc(profile)}" data-document-intent="{esc(intent)}"><head><meta charset="utf-8"><meta name="omega:surface" content="document"><meta name="omega:theme_profile" content="{esc(profile)}"><meta name="omega:language" content="{esc(lang)}"><meta name="omega:direction" content="{esc(direction)}"><meta name="omega:source_count" content="{len(truth.get("sources", []))}"><meta name="omega:claim_count" content="{len(truth.get("claims", []))}"><title>{esc(title)}</title><style>{css}</style></head><body><div class="page"><header><div class="masthead"><span class="eyebrow">Ω Omega</span><span class="document-label">{esc(DOC_LABELS.get("ar" if lang == "ar" else "en", {}).get(intent, "Omega document"))}</span></div><h1 {hero_attrs}>{hero_trace}{esc(title)}</h1><p class="lede" {sub_attrs}>{sub_trace}{esc(subheadline.get("text", "") if subheadline else "")}</p></header><main class="{main_class}"><div class="content">{"".join(sections)}</div>{rail_html}</main><footer>{esc(footer)}</footer></div></body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--surface-profile", choices=sorted(THEMES), default=None)
    args = parser.parse_args()
    bundle = load_bundle(args.bundle)
    errors = truthlock(bundle)
    if errors:
        print(json.dumps({"status": "REJECT", "errors": errors}, ensure_ascii=False))
        return 2
    profile = args.surface_profile or bundle["reader"].get("surface_profile", "omega-editorial")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(bundle, profile), encoding="utf-8")
    print(json.dumps({"status": "PASS", "path": str(output), "surface_profile": profile}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
