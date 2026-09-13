#!/usr/bin/env python3
"""Render a semantic Omega bundle as a calm, document-first HTML artifact."""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEMES = {
    "omega-editorial": {
        "bg": "#f3eee6", "surface": "#fffdf9", "ink": "#202522", "muted": "#66706b",
        "accent": "#9b563d", "soft": "#eee3d8", "line": "#d8d0c5",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-minimal": {
        "bg": "#f4f7f5", "surface": "#ffffff", "ink": "#15221f", "muted": "#61706b",
        "accent": "#147b70", "soft": "#e2efeb", "line": "#d4e0dc",
        "display": "'Noto Sans Arabic', Arial, sans-serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-hud": {
        "bg": "#0b1114", "surface": "#111c20", "ink": "#edf5f2", "muted": "#a9bab5",
        "accent": "#62ddbd", "soft": "#173a38", "line": "#2b4743",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "aion": {
        "bg": "#071016", "surface": "#101d23", "ink": "#edfaff", "muted": "#a7bec5",
        "accent": "#42d9ee", "soft": "#12333a", "line": "#2b4d57",
        "display": "'Segoe UI', Arial, sans-serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-gold": {
        "bg": "#080b0e", "surface": "#13171c", "ink": "#f5eee3", "muted": "#b8aa98",
        "accent": "#e3b56a", "soft": "#242018", "line": "#4a3d2b",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-teal": {
        "bg": "#071013", "surface": "#102024", "ink": "#ecf7f5", "muted": "#a6bbb8",
        "accent": "#59d9c1", "soft": "#153a38", "line": "#2c514c",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-cyan": {
        "bg": "#061018", "surface": "#0e1b25", "ink": "#effaff", "muted": "#a5c3cc",
        "accent": "#51d4f2", "soft": "#123441", "line": "#2a5363",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
}

INTENT_LABELS = {
    "ar": {
        "verdict": "الحكم الحالي", "narrative": "السياق", "key_fact": "حقائق أساسية",
        "comparison": "مقارنة", "evidence_matrix": "مصفوفة الأدلة", "risk_register": "المخاطر المفتوحة",
        "sequence": "تسلسل المتابعة", "checklist": "الخطوات التالية", "table": "جدول الحالة",
        "callout": "تنبيه", "technical_block": "تفصيل تقني", "technical_annex": "الملحق التقني",
        "source_ledger": "سجل المصادر",
    },
    "en": {
        "verdict": "Current decision", "narrative": "Context", "key_fact": "Key facts",
        "comparison": "Comparison", "evidence_matrix": "Evidence matrix", "risk_register": "Open risks",
        "sequence": "Sequence", "checklist": "Next steps", "table": "Status table",
        "callout": "Note", "technical_block": "Technical detail", "technical_annex": "Technical annex",
        "source_ledger": "Source ledger",
    },
}

DOC_LABELS = {
    "ar": {"audit_report": "مراجعة حقيقة تشغيلية", "proposal": "مقترح قرار", "technical": "تقرير تقني"},
    "en": {"audit_report": "Operational truth review", "proposal": "Decision proposal", "technical": "Technical report"},
}

AR_TECH_LABELS = {
    "Environment": "البيئة", "Evidence status": "حالة الدليل", "Observed command": "الأمر المرصود",
    "Release caveat": "ملاحظة الإصدار", "Technical annex": "الملحق التقني", "Source ledger": "سجل المصادر",
    "Path": "المسار", "Version": "الإصدار", "Database": "قاعدة البيانات", "Check": "الفحص",
    "Observed": "المرصود", "State": "الحالة", "Runtime check": "فحص التشغيل",
    "Static asset path": "مسار الملفات الثابتة", "Annex": "الملحق", "Release note": "ملاحظة الإصدار",
    "Runtime brief": "ملخص التشغيل", "Check result": "نتيجة الفحص",
}


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


def document_kind(bundle):
    intent = bundle["reader"].get("document_intent", "report")
    return {"audit_report": "audit", "proposal": "proposal", "technical": "technical"}.get(intent, "report")


def localize(value, lang):
    if lang == "ar":
        return AR_TECH_LABELS.get(value, value)
    return value


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


def render_structured(block, lang):
    kind = block["type"]
    title = f'<h3 class="structured-title">{esc(localize(block["title"], lang))}</h3>' if block.get("title") else ""
    attrs = structured_attrs(block)
    if kind == "fact_list":
        rows = []
        for item in block.get("items", []):
            detail = f'<small>{esc(item["detail"])}</small>' if item.get("detail") else ""
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            rows.append(f'<div class="fact" {linked}><dt>{esc(localize(item["label"], lang))}</dt><dd>{esc(item["value"])}{detail}</dd></div>')
        return f'<dl class="structured structured--facts" {attrs}>{title}{"".join(rows)}</dl>'
    if kind in {"table", "comparison"}:
        columns = [localize(column, lang) for column in block.get("columns", [])]
        head = "".join(f'<th scope="col">{esc(column)}</th>' for column in columns)
        rows = []
        for row in block.get("rows", []):
            linked = refs_attrs(row.get("claim_refs"), row.get("copy_refs"))
            cells = "".join(f'<td data-label="{esc(columns[index] if index < len(columns) else "")}">{esc(localize(cell, lang))}</td>' for index, cell in enumerate(row.get("cells", [])))
            rows.append(f'<tr {linked}>{cells}</tr>')
        return f'<div class="structured structured--{esc(kind)}" {attrs}>{title}<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>'
    if kind in {"sequence", "checklist"}:
        items = []
        for item in block.get("items", []):
            detail = f'<span>{esc(item.get("detail") or item.get("value", ""))}</span>' if item.get("detail") or item.get("value") else ""
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            items.append(f'<li {linked}><strong>{esc(localize(item["label"], lang))}</strong>{detail}</li>')
        tag = "ol" if kind == "sequence" else "ul"
        return f'<div class="structured structured--{esc(kind)}" {attrs}>{title}<{tag}>{"".join(items)}</{tag}></div>'
    if kind == "risk_register":
        items = []
        for item in block.get("items", []):
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            detail = f'<p>{esc(item["detail"])}</p>' if item.get("detail") else ""
            items.append(f'<article class="risk" {linked}><strong>{esc(localize(item["label"], lang))}</strong><span>{esc(localize(item["value"], lang))}</span>{detail}</article>')
        return f'<div class="structured structured--risk" {attrs}>{title}{"".join(items)}</div>'
    if kind == "code":
        return f'<div class="structured structured--code" {attrs}>{title}<pre><code dir="ltr">{esc(block.get("code", ""))}</code></pre></div>'
    if kind == "source_ledger":
        items = []
        for item in block.get("items", []):
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            items.append(f'<li {linked}><strong>{esc(localize(item["label"], lang))}</strong><span>{esc(item["value"])}</span></li>')
        return f'<div class="structured structured--ledger" {attrs}>{title}<ol>{"".join(items)}</ol></div>'
    if kind == "callout":
        return f'<aside class="structured structured--callout" {attrs}>{title}<p>{esc(block.get("code", ""))}</p></aside>'
    return ""


def stylesheet(theme):
    return f'''\n:root{{--bg:{theme["bg"]};--surface:{theme["surface"]};--ink:{theme["ink"]};--muted:{theme["muted"]};--accent:{theme["accent"]};--soft:{theme["soft"]};--line:{theme["line"]};--display:{theme["display"]};--body:{theme["body"]}}}
*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.7}}.page{{max-width:1360px;margin:auto;padding:0 clamp(22px,5vw,86px)}}.hero{{padding:22px 0 clamp(42px,7vw,82px);border-bottom:1px solid var(--line)}}.hero-meta{{display:flex;justify-content:space-between;align-items:center;gap:20px;color:var(--muted);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase}}.brandmark{{color:var(--accent);font-weight:800}}.document-label{{font-weight:700}}.hero-grid{{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(220px,.45fr);gap:clamp(30px,7vw,110px);align-items:end;margin-top:clamp(34px,6vw,70px)}}.hero-copy{{min-width:0}}.eyebrow,.section-kicker{{color:var(--accent);font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}}h1,h2,h3{{font-family:var(--display);line-height:1.14}}h1{{font-size:clamp(2.7rem,6.3vw,5.35rem);letter-spacing:-.045em;max-width:15ch;margin:10px 0 20px}}.lede{{max-width:64ch;color:var(--muted);font-size:1.06rem;margin:0}}.summary-note{{border-top:2px solid var(--accent);padding-top:13px;max-width:280px;color:var(--muted);font-size:.88rem}}.summary-note h2{{font-size:1.08rem;color:var(--ink);margin:0 0 7px}}.summary-note p{{margin:0}}.document-grid{{display:grid;grid-template-columns:minmax(210px,.36fr) minmax(0,1fr);gap:clamp(30px,6vw,96px);padding:0}}.section{{display:contents}}.section-heading,.section-body{{border-bottom:1px solid var(--line);padding:clamp(38px,6vw,72px) 0}}.section-heading{{grid-column:1;grid-row:auto;align-self:start}}.section-body{{grid-column:2;min-width:0}}.section-heading h2{{font-size:clamp(1.5rem,2.45vw,2.35rem);letter-spacing:-.025em;margin:10px 0 0;max-width:18ch}}.copy{{max-width:68ch;margin:0 0 18px}}.copy--callout,.callout{{border-inline-start:3px solid var(--accent);background:var(--soft);padding:16px 20px;margin:0 0 22px;max-width:72ch}}.structured-title{{font-family:var(--body);font-size:.78rem;color:var(--muted);font-weight:800;letter-spacing:.05em;margin:0 0 14px;text-transform:uppercase}}.structured--facts{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:2px solid var(--accent);margin:22px 0 0}}.fact{{padding:17px 18px 19px 0;border-bottom:1px solid var(--line);min-width:0}}[dir="ltr"] .fact{{padding-inline:0 18px}}.fact dt{{color:var(--muted);font-size:.78rem;margin-bottom:4px}}.fact dd{{font-size:1.06rem;font-weight:800;margin:0;overflow-wrap:anywhere}}.fact small{{display:block;color:var(--muted);font-size:.78rem;font-weight:400;margin-top:4px}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;border-top:2px solid var(--accent);font-size:.94rem}}th,td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:start;vertical-align:top}}th{{color:var(--muted);font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}}td:first-child{{font-weight:700}}.structured--comparison table{{border-inline-start:3px solid var(--accent)}}.structured--sequence ol,.structured--checklist ul,.structured--ledger ol{{list-style:none;margin:0;padding:0}}.structured--sequence li,.structured--checklist li{{display:grid;grid-template-columns:42px minmax(0,1fr);gap:14px;border-bottom:1px solid var(--line);padding:14px 0}}.structured--sequence li::before{{counter-increment:item;content:counter(item,decimal-leading-zero);color:var(--accent);font-size:1.05rem;font-weight:800}}.structured--sequence ol{{counter-reset:item}}.structured--sequence li strong,.structured--checklist li strong{{display:block}}.structured--sequence li span,.structured--checklist li span{{grid-column:2;color:var(--muted);font-size:.9rem}}.structured--checklist li::before{{content:"□";font-size:1.15rem;color:var(--accent)}}.structured--risk{{display:grid;gap:0;border-top:2px solid var(--accent)}}.risk{{display:grid;grid-template-columns:minmax(150px,.35fr) minmax(130px,.28fr) minmax(0,1fr);gap:18px;border-bottom:1px solid var(--line);padding:16px 0;align-items:start}}.risk span{{color:var(--accent);font-size:.84rem;font-weight:800}}.risk p{{color:var(--muted);margin:0}}.structured--code,.technical-copy{{background:var(--surface);border:1px solid var(--line);padding:18px 20px;overflow:auto}}.structured--code{{margin-top:18px}}pre{{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:.86rem/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;direction:ltr;text-align:left}}.structured--ledger{{border-top:2px solid var(--accent)}}.structured--ledger li{{display:grid;grid-template-columns:minmax(145px,.36fr) minmax(0,1fr);gap:18px;padding:13px 0;border-bottom:1px solid var(--line)}}.structured--ledger span{{color:var(--muted)}}footer{{padding:22px 0 36px;color:var(--muted);font-size:.76rem;border-top:1px solid var(--line)}}[dir="rtl"] .technical-copy,[dir="rtl"] .structured--code{{direction:ltr;text-align:left}}@media(max-width:820px){{body{{font-size:15px}}.page{{padding:0 18px}}.hero{{padding-bottom:38px}}.hero-meta{{align-items:flex-start;font-size:.62rem}}.hero-grid{{display:block;margin-top:34px}}h1{{font-size:clamp(2.45rem,12vw,4rem);max-width:17ch;margin-bottom:16px}}.lede{{font-size:.98rem}}.summary-note{{margin-top:30px;max-width:none}}.document-grid{{display:block}}.section{{display:block}}.section-heading,.section-body{{padding:34px 0}}.section-heading{{border-bottom:0;padding-bottom:9px}}.section-heading h2{{font-size:1.7rem;max-width:none}}.section-body{{padding-top:0}}.structured--facts{{grid-template-columns:repeat(2,minmax(0,1fr))}}.fact{{padding-inline:0 14px}}.fact:nth-child(even){{padding-inline:14px 0;border-inline-start:1px solid var(--line)}}table{{font-size:.88rem}}table thead{{display:none}}table,tbody,tr,td{{display:block;width:100%}}tr{{padding:10px 0;border-bottom:1px solid var(--line)}}td{{display:grid;grid-template-columns:minmax(100px,.34fr) minmax(0,1fr);gap:12px;padding:8px 0;border:0}}td::before{{content:attr(data-label);color:var(--muted);font-size:.7rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase}}.risk{{grid-template-columns:minmax(110px,.35fr) minmax(0,1fr);gap:8px 14px}}.risk p{{grid-column:1 / -1}}.structured--ledger li{{grid-template-columns:1fr;gap:3px}}footer{{padding-bottom:24px}}}}@media print{{@page{{size:A4;margin:15mm}}html,body{{background:#fff;color:#171717}}html[data-surface-profile="omega-hud"],html[data-surface-profile="aion"]{{--surface:#fff;--bg:#fff;--ink:#171717;--muted:#555;--accent:#333;--soft:#f1f1f1;--line:#c8c8c8}}.page{{max-width:none;padding:0}}.hero{{padding:5mm 0 9mm}}.hero-grid{{margin-top:8mm}}h1{{font-size:30pt}}.summary-note{{max-width:230px}}.document-grid{{display:grid;grid-template-columns:28% 1fr;gap:10%}}.section-heading,.section-body{{padding:7mm 0}}table{{font-size:9pt}}.table-wrap{{overflow:visible}}.structured--technical_annex{{break-before:page}}.structured--code,.technical-copy{{background:#fff}}footer{{padding-top:6mm}}}}'''


def render(bundle, profile=None):
    truth, authored, composition, reader = bundle["truth"], bundle["authored"], bundle["composition"], bundle["reader"]
    profile = profile or reader.get("surface_profile", "omega-editorial")
    theme = THEMES[profile]
    lang = reader.get("language", {}).get("primary", "en")
    direction = reader.get("language", {}).get("direction", "ltr")
    intent = reader.get("document_intent", "report")
    kind = document_kind(bundle)
    labels = INTENT_LABELS["ar" if lang == "ar" else "en"]
    blocks = {block["copy_id"]: block for block in authored["blocks"]}
    headline = next((block for block in authored["blocks"] if block.get("role") == "headline"), None)
    subheadline = next((block for block in authored["blocks"] if block.get("role") == "subheadline"), None)
    title = headline.get("text", "Omega document") if headline else DOC_LABELS["en"].get(intent, "Omega document")
    hero_attrs = f'data-copy-id="{esc(headline["copy_id"])}" {refs_attrs(headline.get("claim_refs"), [headline["copy_id"]])}' if headline else ""
    hero_trace = "".join(f'<span class="trace-marker" data-claim-id="{esc(ref)}" aria-hidden="true"></span>' for ref in (headline or {}).get("claim_refs", []))
    sub_attrs = f'data-copy-id="{esc(subheadline["copy_id"])}" {refs_attrs(subheadline.get("claim_refs"), [subheadline["copy_id"]])}' if subheadline else ""
    sub_trace = "".join(f'<span class="trace-marker" data-claim-id="{esc(ref)}" aria-hidden="true"></span>' for ref in (subheadline or {}).get("claim_refs", []))
    rail = reader.get("summary_rail", {})
    note = f'<aside class="summary-note"><h2>{esc(localize(rail.get("title", ""), lang))}</h2><p>{esc(rail.get("body", ""))}</p></aside>' if rail.get("enabled") else ""
    sections = []
    for section in composition["sections"]:
        section_intent = section["presentation_intent"]
        section_label = labels.get(section_intent, section_intent)
        copy_html = "".join(render_copy(blocks[ref], section_intent) for ref in section.get("copy_refs", []) if ref in blocks and blocks[ref].get("role") not in {"headline", "subheadline"})
        structured_html = "".join(render_structured(block, lang) for block in section.get("structured_blocks", []))
        attrs = f'data-section-id="{esc(section["section_id"])}" data-presentation-intent="{esc(section_intent)}"'
        sections.append(f'<section class="section section--{esc(section_intent)}" {attrs}><div class="section-heading"><div class="section-kicker">{esc(section_label)}</div><h2>{esc(section["purpose"])}</h2></div><div class="section-body">{copy_html}{structured_html}</div></section>')
    footer = "مستند مستقل؛ محتواه قابل للتدقيق من خلال سجل المصادر." if lang == "ar" else "Standalone document; content is traceable through the source ledger."
    css = stylesheet(theme).replace("}}", "}").replace('html[data-surface-profile="omega-hud"],html[data-surface-profile="aion"]', ":root").replace('html[data-surface-profile="omega-hud"],html[data-surface-profile="aion"],html[data-surface-profile="omega-gold"],html[data-surface-profile="omega-teal"],html[data-surface-profile="omega-cyan"]', ":root")
    css += '\n@media screen{.hero-grid{margin-top:clamp(28px,4vw,52px)}h1{font-size:clamp(2.45rem,5.2vw,4.6rem);max-width:21ch}.document-grid--proposal .section-heading,.document-grid--proposal .section-body{padding-block:clamp(28px,4vw,48px)}.document-grid--proposal .section-heading h2{font-size:clamp(1.35rem,2vw,2rem)} } @media screen and (max-width:820px){h1{font-size:clamp(2.1rem,10vw,3.35rem);max-width:19ch}.hero{padding-bottom:32px} } @media print{.document-grid{display:block}.section{display:grid;grid-template-columns:28% 1fr;gap:10%;break-inside:avoid}.section-heading,.section-body{grid-column:auto;grid-row:auto} }'
    return f'''<!doctype html><html lang="{esc(lang)}" dir="{esc(direction)}" data-surface-profile="{esc(profile)}" data-document-intent="{esc(intent)}" data-document-kind="{esc(kind)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="omega:surface" content="document"><meta name="omega:brand_profile" content="omega-default"><meta name="omega:page_size" content="A4"><meta name="omega:page_intent" content="print_and_pdf"><meta name="omega:theme_profile" content="{esc(profile)}"><meta name="omega:language" content="{esc(lang)}"><meta name="omega:direction" content="{esc(direction)}"><meta name="omega:source_count" content="{len(truth.get("sources", []))}"><meta name="omega:claim_count" content="{len(truth.get("claims", []))}"><title>{esc(title)}</title><style>{css}</style></head><body><div class="page"><header class="hero hero--{esc(kind)}"><div class="hero-meta"><span class="brandmark">Ω OMEGA</span><span class="document-label">{esc(DOC_LABELS.get("ar" if lang == "ar" else "en", {}).get(intent, "Omega document"))}</span></div><div class="hero-grid"><div class="hero-copy"><h1 {hero_attrs}>{hero_trace}{esc(title)}</h1><p class="lede" {sub_attrs}>{sub_trace}{esc(subheadline.get("text", "") if subheadline else "")}</p></div>{note}</div></header><main class="document-grid document-grid--{esc(kind)}">{"".join(sections)}</main><footer>{esc(footer)}</footer></div></body></html>'''


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
