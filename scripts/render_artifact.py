#!/usr/bin/env python3
"""Render a semantic Omega bundle as a screen-first, human-facing HTML artifact."""
import argparse
import base64
import html
import json
import re
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
        "bg": "#060a0c", "surface": "#0d1418", "ink": "#edf4f1", "muted": "#8fa3a0",
        "accent": "#4fb8a7", "soft": "#112624", "line": "#28403d",
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
        "bg": "#05080b", "surface": "#0b1015", "ink": "#f3eee5", "muted": "#8f9997",
        "accent": "#c89545", "soft": "#15130f", "line": "#2e302f",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-teal": {
        "bg": "#04090b", "surface": "#091316", "ink": "#e6f0ed", "muted": "#8ea7a2",
        "accent": "#3aaf9c", "soft": "#0d2625", "line": "#21403d",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
    "omega-cyan": {
        "bg": "#04090f", "surface": "#08141b", "ink": "#e7f3f7", "muted": "#8ca9b2",
        "accent": "#2ea9c5", "soft": "#0b2733", "line": "#1e4251",
        "display": "Georgia, 'Noto Serif Arabic', serif", "body": "'Noto Sans Arabic', Arial, sans-serif",
    },
}

INTENT_LABELS = {
    "ar": {
        "verdict": "الحكم الحالي", "narrative": "السياق", "key_fact": "حقائق أساسية",
        "comparison": "مقارنة", "evidence_matrix": "مصفوفة الأدلة", "risk_register": "المخاطر المفتوحة",
        "timeline": "خط زمني مشروط",
        "sequence": "تسلسل المتابعة", "checklist": "الخطوات التالية", "table": "جدول الحالة",
        "callout": "تنبيه", "technical_block": "تفصيل تقني", "technical_annex": "الملحق التقني",
        "source_ledger": "سجل المصادر",
    },
    "en": {
        "verdict": "Current decision", "narrative": "Context", "key_fact": "Key facts",
        "comparison": "Comparison", "evidence_matrix": "Evidence matrix", "risk_register": "Open risks",
        "timeline": "Conditional timeline",
        "sequence": "Sequence", "checklist": "Next steps", "table": "Status table",
        "callout": "Note", "technical_block": "Technical detail", "technical_annex": "Technical annex",
        "source_ledger": "Source ledger",
    },
}

DOC_LABELS = {
    "ar": {"audit_report": "مراجعة تشغيلية", "proposal": "ملخص قرار", "technical": "فحص تقني"},
    "en": {"audit_report": "Operational review", "proposal": "Decision brief", "technical": "Technical check"},
}

AR_TECH_LABELS = {
    "Environment": "البيئة", "Evidence status": "حالة الدليل", "Observed command": "الأمر المرصود",
    "Release caveat": "ملاحظة الإصدار", "Technical annex": "الملحق التقني", "Source ledger": "سجل المصادر",
    "Path": "المسار", "Version": "الإصدار", "Database": "قاعدة البيانات", "Check": "الفحص",
    "Observed": "المرصود", "State": "الحالة", "Runtime check": "فحص التشغيل",
    "Static asset path": "مسار الملفات الثابتة", "Annex": "الملحق", "Release note": "ملاحظة الإصدار",
    "Runtime brief": "ملخص التشغيل", "Check result": "نتيجة الفحص",
}

HUD_LABELS = {
        "ar": {"sources": "مصادر", "claims": "مطالبة", "signals": "إشارات القرار", "surface": "واجهة تنفيذية"},
    "en": {"sources": "Sources", "claims": "Claims", "signals": "Decision signals", "surface": "Executive surface"},
}

HUD_PROFILE_LABELS = {
    "omega-editorial": "EDITORIAL",
    "omega-minimal": "MINIMAL",
    "omega-hud": "HUD TEAL",
    "aion": "AION CYAN",
    "omega-gold": "HUD GOLD",
    "omega-teal": "HUD TEAL",
    "omega-cyan": "HUD CYAN",
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


def favicon_data_uri(theme):
    icon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="16" fill="{theme["bg"]}"/>'
        f'<text x="32" y="48" text-anchor="middle" font-family="Georgia,serif" '
        f'font-size="42" font-weight="700" fill="{theme["accent"]}">Ω</text></svg>'
    )
    return base64.b64encode(icon_svg.encode("utf-8")).decode("ascii")


def preloader_markup():
    return '''<div id="omega-preloader" class="omega-preloader" role="status" aria-live="polite" aria-label="Loading Omega">
  <div class="omega-preloader__inner">
    <div class="omega-preloader__mark" aria-hidden="true"><span>Ω</span></div>
    <div class="omega-preloader__brand">Ω OMEGA</div>
    <div class="omega-preloader__name">Jemy</div>
    <div class="omega-preloader__rule" aria-hidden="true"><span></span></div>
  </div>
</div>
<script>
(() => {
  const preloader = document.getElementById("omega-preloader");
  const startedAt = performance.now();
  const minimumVisibleMs = 1200;
  const dismiss = () => {
    document.documentElement.classList.add("omega-ready");
    if (!preloader) return;
    preloader.classList.add("omega-preloader--hidden");
    window.setTimeout(() => preloader.remove(), 520);
  };
  const ready = () => {
    const remaining = Math.max(0, minimumVisibleMs - (performance.now() - startedAt));
    window.setTimeout(() => window.requestAnimationFrame(dismiss), remaining);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready, {once: true});
  } else {
    ready();
  }
})();
</script>'''


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


def hud_signal_tiles(bundle, lang):
    """Promote existing fact-list values into a traceable executive signal row."""
    fact_blocks = []
    for section in bundle["composition"].get("sections", []):
        for block in section.get("structured_blocks", []):
            if block.get("type") == "fact_list":
                fact_blocks.append(block)
    if fact_blocks:
        block = max(fact_blocks, key=lambda candidate: len(candidate.get("items", [])))
        tiles = []
        for item in block.get("items", [])[:4]:
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            detail = f'<small>{esc(item["detail"])}</small>' if item.get("detail") else ""
            tiles.append(
                f'<div class="hud-signal" {linked}>'
                f'<span class="hud-signal-label">{esc(localize(item["label"], lang))}</span>'
                f'<strong>{esc(item["value"])}</strong>{detail}</div>'
            )
        return "".join(tiles)
    return ""


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


def metric_parts(value):
    match = re.match(r"^(≈\s*)?([\d,]+h?)(?:\s+(.*))?$", value.strip())
    if not match:
        match = re.match(r"^([\d,]+)(?:\s+(.*))?$", value.strip())
    if not match:
        return value, ""
    number = (match.group(1) or "") + match.group(2)
    return number.strip(), (match.group(3) or "").strip()


def render_structured(block, lang, section_id=None, baseline=""):
    kind = block["type"]
    title = f'<h3 class="structured-title">{esc(localize(block["title"], lang))}</h3>' if block.get("title") else ""
    attrs = structured_attrs(block)
    if kind == "fact_list":
        if section_id == "facts" and block.get("block_id") == "STRUCT.AHS.FACTS":
            cards = []
            for item in block.get("items", []):
                number, context = metric_parts(item["value"])
                if item["label"] == "مرشحو التداخل":
                    context = "مرشح تداخل · National_ID"
                linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
                cards.append(
                    f'<article class="metric-card" data-metric-value="{esc(number)}" {linked}>'
                    f'<span class="metric-label">{esc(localize(item["label"], lang))}</span>'
                    f'<strong class="metric-value">{esc(number)}</strong>'
                    f'<span class="metric-context">{esc(localize(context, lang))}</span></article>'
                )
            return f'<div class="structured structured--metrics" {attrs}><div class="metric-grid">{title}{"".join(cards)}</div></div>'
        if section_id == "effort":
            cards = []
            for index, item in enumerate(block.get("items", []), start=1):
                parts = [part.strip() for part in item["value"].split("·", 1)]
                cadence, duration = (parts + [""])[:2]
                linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
                cards.append(
                    f'<article class="mode-card mode-card--{esc(item["label"].lower())}" {linked}>'
                    f'<span class="mode-index">{index:02d}</span><span class="mode-name">{esc(item["label"])}</span>'
                    f'<strong class="mode-value">{esc(cadence)}</strong><span class="mode-duration">{esc(duration)}</span>'
                    f'<p>{esc(item.get("detail", ""))}</p><span class="mode-state">{esc("مشروط" if lang == "ar" else "Conditional")}</span></article>'
                )
            baseline_html = (
                f'<div class="effort-baseline"><span>{esc("خط الأساس التخطيطي" if lang == "ar" else "Planning baseline")}</span><strong>{esc(baseline or "120h")}</strong>'
                f'<small>{esc("المعيار ثابت مهما تغيّرت الوتيرة" if lang == "ar" else "The acceptance standard stays fixed as the pace changes")}</small></div>'
            )
            return f'<div class="structured structured--effort" {attrs}><div class="effort-snapshot">{title}{baseline_html}<div class="mode-grid">{"".join(cards)}</div></div></div>'
        if section_id == "decision":
            rows = []
            for item in block.get("items", []):
                linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
                rows.append(
                    f'<div class="verdict-row" {linked}><span>{esc(localize(item["label"], lang))}</span>'
                    f'<strong>{esc(localize(item["value"], lang))}</strong></div>'
                )
            return f'<div class="structured structured--verdict" {attrs}><div class="verdict-readout">{title}{"".join(rows)}</div></div>'
        rows = []
        for item in block.get("items", []):
            detail = f'<small>{esc(item["detail"])}</small>' if item.get("detail") else ""
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            rows.append(f'<div class="fact" {linked}><dt>{esc(localize(item["label"], lang))}</dt><dd>{esc(item["value"])}{detail}</dd></div>')
        return f'<dl class="structured structured--facts" {attrs}>{title}{"".join(rows)}</dl>'
    if kind == "timeline":
        status_classes = {"مُثبت": "passed", "مفتوح": "open", "محجوب": "blocked", "مشروط": "conditional", "Passed": "passed", "Open": "open", "Blocked": "blocked", "Conditional": "conditional"}
        steps = []
        for index, item in enumerate(block.get("items", []), start=1):
            state = item.get("value", "مفتوح")
            data_state = {"مُثبت": "passed", "مفتوح": "open", "محجوب": "blocked", "مشروط": "conditional", "Passed": "passed", "Open": "open", "Blocked": "blocked", "Conditional": "conditional"}.get(state, "open")
            status_label = "✓ مُثبت" if lang == "ar" and state == "مُثبت" else ("✓ Passed" if lang == "en" and state == "Passed" else localize(state, lang))
            linked = refs_attrs(item.get("claim_refs"), item.get("copy_refs"))
            steps.append(
                f'<li class="timeline-step timeline-step--{status_classes.get(state, "open")}" data-state="{data_state}" {linked}>'
                f'<span class="timeline-marker"><span>{index:02d}</span></span><div class="timeline-content">'
                f'<div class="timeline-topline"><strong>{esc(localize(item["label"], lang))}</strong><span class="status-indicator">{esc(status_label)}</span></div>'
                f'<p>{esc(item.get("detail", ""))}</p></div></li>'
            )
        return f'<div class="structured structured--timeline" {attrs}><div class="timeline-track">{title}<ol>{"".join(steps)}</ol></div></div>'
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


def hud_stylesheet_overrides():
    return '''
:root {--hud-radius-xl:30px;--hud-radius-lg:22px;--hud-radius-md:16px;--hud-shadow:0 26px 70px rgba(0,0,0,.28)}
.omega-preloader {position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:var(--bg);color:var(--ink);transition:opacity .42s ease,visibility .42s ease}
.omega-preloader--hidden {opacity:0;visibility:hidden;pointer-events:none}
.omega-preloader__inner {position:relative;display:grid;justify-items:center;gap:10px;min-width:190px;padding:30px 34px 26px;border:1px solid color-mix(in srgb,var(--accent) 48%,var(--line));border-radius:var(--hud-radius-lg);background:linear-gradient(145deg,color-mix(in srgb,var(--surface) 88%,var(--bg)),var(--surface));box-shadow:0 24px 70px rgba(0,0,0,.32),0 0 70px color-mix(in srgb,var(--accent) 12%,transparent);overflow:hidden;animation:omega-preloader-in .6s cubic-bezier(.2,.75,.25,1) both}
.omega-preloader__inner::before {content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(circle at 50% 0,color-mix(in srgb,var(--accent) 20%,transparent),transparent 58%)}
.omega-preloader__mark,.omega-preloader__brand,.omega-preloader__name,.omega-preloader__rule {position:relative;z-index:1}
.omega-preloader__mark {display:grid;place-items:center;width:58px;height:58px;border:1px solid var(--accent);border-radius:50%;color:var(--accent);font:700 2rem/1 Georgia,serif;box-shadow:0 0 0 7px color-mix(in srgb,var(--accent) 8%,transparent),0 0 34px color-mix(in srgb,var(--accent) 24%,transparent);animation:omega-preloader-pulse 1.8s ease-in-out infinite}
.omega-preloader__brand {color:var(--ink);font-size:.78rem;font-weight:900;letter-spacing:.2em}
.omega-preloader__name {color:var(--accent);font-size:.72rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.omega-preloader__rule {width:86px;height:2px;margin-top:5px;background:var(--line);overflow:hidden}
.omega-preloader__rule span {display:block;width:42%;height:100%;background:var(--accent);animation:omega-preloader-progress 1.3s ease-in-out infinite}
.hud-page {position:relative;isolation:isolate}
.hud-page::before {content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.16;background:linear-gradient(90deg,transparent 49.9%,var(--accent) 50%,transparent 50.1%),linear-gradient(0deg,transparent 49.9%,var(--accent) 50%,transparent 50.1%);background-size:72px 72px;mask-image:linear-gradient(to bottom,black,transparent 72%)}
.hud-page .page {position:relative;z-index:1}
.hud-topbar {position:sticky;top:12px;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:18px;margin:18px 0 8px;padding:12px 16px;border:1px solid color-mix(in srgb,var(--accent) 38%,var(--line));border-radius:var(--hud-radius-lg);background:color-mix(in srgb,var(--surface) 88%,var(--bg));box-shadow:var(--hud-shadow);backdrop-filter:blur(16px);font-size:.72rem;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;animation:omega-topbar-in .55s cubic-bezier(.2,.75,.25,1) both}
.hud-brand,.hud-topbar-meta {display:flex;align-items:center;gap:12px}
.hud-brand > span {color:var(--accent);font-weight:900;letter-spacing:.16em}
.hud-brand small {font-size:.64rem;color:var(--muted)}
.hud-topbar-meta > span {padding-inline-start:12px;border-inline-start:1px solid var(--line)}
.hud-topbar-meta .hud-status {color:var(--accent);font-weight:800}
.hud-page .hero {padding:20px 0 34px;border:0}
.hero-surface {position:relative;overflow:hidden;padding:clamp(24px,4vw,52px);border:1px solid color-mix(in srgb,var(--accent) 30%,var(--line));border-radius:var(--hud-radius-xl);background:linear-gradient(145deg,color-mix(in srgb,var(--surface) 94%,var(--bg)),var(--surface));box-shadow:var(--hud-shadow);perspective:1200px;transform-style:preserve-3d;animation:omega-surface-in .75s cubic-bezier(.2,.75,.25,1) .08s both}
.hero-surface::before {content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(circle at 82% 0,color-mix(in srgb,var(--accent) 16%,transparent),transparent 38%),linear-gradient(120deg,transparent 0 62%,color-mix(in srgb,var(--accent) 5%,transparent) 62% 62.2%,transparent 62.2%)}
.hero-surface::after {content:"";position:absolute;top:-28%;inset-inline-end:-9%;width:54%;aspect-ratio:1.8;border:1px solid color-mix(in srgb,var(--accent) 20%,transparent);border-radius:50%;transform:translate3d(0,0,18px) rotate(-14deg);pointer-events:none;opacity:.8;box-shadow:0 0 0 18px color-mix(in srgb,var(--accent) 3%,transparent),0 0 70px color-mix(in srgb,var(--accent) 10%,transparent)}
.hero-surface > * {position:relative;z-index:1}
.hud-page .hero-meta {margin-bottom:clamp(28px,4vw,48px)}
.hud-page .hero-grid {margin-top:0;grid-template-columns:minmax(0,1.35fr) minmax(250px,.65fr);gap:clamp(28px,6vw,88px)}
.hud-page h1 {font-size:clamp(2.8rem,6.2vw,5.35rem);max-width:14ch;text-wrap:balance}
.hud-page .summary-note {max-width:none;margin:0;padding:16px 18px;border:1px solid var(--line);border-top:2px solid var(--accent);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--soft) 74%,var(--surface));box-shadow:0 12px 30px rgba(0,0,0,.12)}
.hud-metrics {display:grid;grid-template-columns:minmax(130px,.4fr) repeat(4,minmax(0,1fr));gap:12px;margin-top:clamp(28px,5vw,54px);padding-top:18px;border-top:1px solid var(--line)}
.hud-metrics-label {align-self:center;color:var(--accent);font-size:.68rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase}
.hud-signal {min-height:92px;padding:14px 16px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 78%,transparent);display:flex;flex-direction:column;justify-content:center;gap:3px;transform:translateZ(0);transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease,background-color .25s ease;animation:omega-signal-in .6s cubic-bezier(.2,.75,.25,1) both}
.hud-signal:nth-child(2) {animation-delay:.18s}
.hud-signal:nth-child(3) {animation-delay:.26s}
.hud-signal:nth-child(4) {animation-delay:.34s}
.hud-signal:nth-child(5) {animation-delay:.42s}
.hud-signal:hover {transform:translate3d(0,-5px,18px) rotateX(1deg);border-color:var(--accent);background:color-mix(in srgb,var(--surface) 92%,var(--accent) 8%);box-shadow:0 18px 34px rgba(0,0,0,.22)}
.hud-signal:focus-visible {outline:2px solid var(--accent);outline-offset:3px}
.hud-signal-label {color:var(--muted);font-size:.7rem}
.hud-signal strong {font-size:1.15rem;line-height:1.25;overflow-wrap:anywhere}
.hud-signal small {color:var(--muted);font-size:.72rem}
.hud-page .document-grid {padding-top:0}
.hud-page .section--verdict .section-body {padding-top:clamp(30px,4vw,52px)}
.hud-page .section--verdict .copy--callout {border:1px solid var(--line);border-inline-start:3px solid var(--accent);border-radius:var(--hud-radius-md);box-shadow:0 12px 28px rgba(0,0,0,.1)}
.hud-page .structured--facts,.hud-page .structured--risk,.hud-page table {border-top-width:2px}
.structured--facts .structured-title {grid-column:1 / -1;margin:0;padding:0 0 10px;line-height:1.4}
.hud-page .structured--facts {padding-top:18px}
.hud-page .fact {padding-block:14px 18px;line-height:1.55}
.hud-page .fact dt {line-height:1.45}
.hud-page .fact dd {line-height:1.4}
@keyframes omega-topbar-in {from {opacity:0;transform:translateY(-10px)} to {opacity:1;transform:translateY(0)}}
@keyframes omega-surface-in {from {opacity:0;transform:translateY(18px) rotateX(1.5deg)} to {opacity:1;transform:translateY(0) rotateX(0)}}
@keyframes omega-signal-in {from {opacity:0;transform:translateY(12px) scale(.98)} to {opacity:1;transform:translateY(0) scale(1)}}
@keyframes omega-preloader-in {from {transform:translateY(12px) scale(.96)} to {transform:translateY(0) scale(1)}}
@keyframes omega-preloader-pulse {0%,100% {transform:scale(1);box-shadow:0 0 0 7px color-mix(in srgb,var(--accent) 8%,transparent),0 0 34px color-mix(in srgb,var(--accent) 24%,transparent)}50% {transform:scale(1.04);box-shadow:0 0 0 11px color-mix(in srgb,var(--accent) 4%,transparent),0 0 48px color-mix(in srgb,var(--accent) 32%,transparent)}}
@keyframes omega-preloader-progress {0% {transform:translateX(-140%)}50%,100% {transform:translateX(330%)}}
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after {animation-duration:.01ms !important;animation-iteration-count:1 !important;scroll-behavior:auto !important;transition-duration:.01ms !important}
  .hud-signal:hover {transform:none}
}
@media screen {
  .hud-page .document-grid {display:block}
  .hud-page .section {position:relative;display:grid;grid-template-columns:minmax(180px,.34fr) minmax(0,1fr);gap:clamp(22px,4vw,60px);margin:0 0 24px;padding:clamp(22px,3vw,34px);border:1px solid var(--line);border-radius:var(--hud-radius-lg);background:var(--surface);background:color-mix(in srgb,var(--surface) 88%,var(--bg));box-shadow:0 18px 42px rgba(0,0,0,.14);overflow:hidden}
  .hud-page .section::before {content:"";position:absolute;inset-inline-start:0;top:0;bottom:0;width:3px;background:var(--accent);opacity:.72}
  .hud-page .section-heading,.hud-page .section-body {border:0;padding:0}
  .hud-page .section-heading {align-self:start;position:relative;z-index:1}
  .hud-page .section-body {min-width:0;position:relative;z-index:1}
  .hud-page .section-heading h2 {margin-top:9px}
  .hud-page .section--verdict {grid-template-columns:minmax(180px,.72fr) minmax(0,1.28fr);background:var(--soft);background:radial-gradient(circle at 100% 0,color-mix(in srgb,var(--accent) 12%,transparent),transparent 42%),var(--soft);border-color:color-mix(in srgb,var(--accent) 46%,var(--line));box-shadow:0 22px 52px rgba(0,0,0,.2)}
  .hud-page .section--verdict .section-heading h2 {font-size:clamp(1.7rem,3vw,2.8rem)}
  .hud-page .section--verdict .copy--callout {margin:0;border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 70%,transparent);box-shadow:0 12px 26px rgba(0,0,0,.14)}
  .hud-page .section--key_fact {background:color-mix(in srgb,var(--surface) 96%,var(--accent) 4%)}
  .hud-page .section--key_fact .structured--facts {padding:14px 18px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 78%,transparent);box-shadow:0 10px 24px rgba(0,0,0,.1)}
  .hud-page .section--evidence_matrix .structured--table,.hud-page .section--evidence_matrix .structured--comparison {padding:16px 18px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 72%,transparent)}
  .hud-page .section--evidence_matrix .structured--table table {border-top:0}
  .hud-page .section--sequence {grid-template-columns:minmax(180px,.55fr) minmax(0,1.45fr);background:color-mix(in srgb,var(--surface) 80%,var(--accent) 4%)}
  .hud-page .section--sequence .structured--sequence {padding:8px 18px;border:1px solid var(--line);border-inline-start:3px solid var(--accent);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 82%,transparent)}
  .hud-page .section--sequence .structured--sequence li {transition:padding-inline .22s ease,background-color .22s ease;border-radius:10px}
  .hud-page .section--sequence .structured--sequence li:hover {padding-inline:10px;background:color-mix(in srgb,var(--accent) 7%,transparent)}
  .hud-page .section--risk_register .risk {margin:10px 0 0;padding:14px 16px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 82%,transparent);transition:transform .22s ease,border-color .22s ease}
  .hud-page .section--risk_register .risk:hover {transform:translateX(-4px);border-color:var(--accent)}
  .hud-page .section--checklist .structured--checklist {padding:8px 18px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 82%,transparent)}
  .hud-page .section--technical_annex {background:#0d1116;border-color:#26303a;box-shadow:0 22px 56px rgba(0,0,0,.28)}
  .hud-page .section--technical_annex .section-heading h2 {color:var(--ink)}
  .hud-page .section--technical_annex .technical-copy,.hud-page .section--technical_annex .structured--code {border-radius:var(--hud-radius-md);background:#070a0e;border-color:#303b47;box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 12px 28px rgba(0,0,0,.22)}
  .hud-page .section--technical_annex .structured--ledger {padding:14px 18px;border:1px solid #303b47;border-radius:var(--hud-radius-md);background:#11171e}
  .hud-page .section--verdict {border-radius:var(--hud-radius-xl) 10px var(--hud-radius-xl) 10px;min-height:250px}
  .hud-page .section--verdict .section-heading {padding-inline-end:12px}
  .hud-page .structured--verdict {height:100%}
  .verdict-readout {display:grid;gap:0;padding:4px 0;border-top:1px solid color-mix(in srgb,var(--accent) 45%,var(--line));border-bottom:1px solid var(--line)}
  .verdict-readout .structured-title {margin:0;padding:14px 0 6px}
  .verdict-row {display:grid;grid-template-columns:minmax(120px,.65fr) minmax(0,1.35fr);gap:18px;padding:15px 0;border-top:1px solid var(--line);align-items:start}
  .verdict-row span {color:var(--muted);font-size:.78rem}
  .verdict-row strong {font-size:1rem;line-height:1.55}
  .hud-page .section--comparison {grid-template-columns:minmax(220px,.72fr) minmax(0,1.28fr);border-radius:10px var(--hud-radius-xl) 10px var(--hud-radius-xl);background:linear-gradient(135deg,color-mix(in srgb,var(--accent) 7%,var(--surface)),var(--surface));border-color:color-mix(in srgb,var(--accent) 40%,var(--line))}
  .hud-page .section--comparison .section-heading h2 {font-size:clamp(1.65rem,2.7vw,2.5rem)}
  .hud-page .section--comparison .section-body {display:flex;flex-direction:column;gap:18px}
  .hud-page .section--comparison .structured--effort {height:auto}
  .effort-snapshot {display:grid;gap:18px;height:auto}
  .effort-snapshot .structured-title {margin:0}
  .effort-baseline {display:grid;grid-template-columns:1fr auto;gap:3px 18px;align-items:center;padding:17px 20px;border:1px solid color-mix(in srgb,var(--accent) 48%,var(--line));border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--soft) 78%,var(--surface));box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
  .effort-baseline span {color:var(--muted);font-size:.75rem}
  .effort-baseline strong {grid-row:span 2;color:var(--accent);font:700 clamp(1.7rem,3.5vw,2.7rem)/1 Georgia,'Noto Serif Arabic',serif;letter-spacing:-.04em}
  .effort-baseline small {color:var(--ink);font-size:.82rem}
  .mode-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
  .mode-card {position:relative;display:flex;flex-direction:column;min-height:190px;padding:17px 16px 16px;border:1px solid var(--line);border-top:2px solid var(--accent);background:color-mix(in srgb,var(--surface) 88%,transparent);box-shadow:0 12px 24px rgba(0,0,0,.15);transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease;background-color .25s ease}
  .mode-card:nth-child(1) {border-radius:var(--hud-radius-md) 8px var(--hud-radius-md) 8px}
  .mode-card:nth-child(2) {border-radius:8px var(--hud-radius-lg) 8px var(--hud-radius-lg);transform:translateY(-8px)}
  .mode-card:nth-child(3) {border-radius:8px var(--hud-radius-md) 8px var(--hud-radius-md)}
  .mode-card:hover,.mode-card:focus-within {transform:translateY(-8px) translateZ(16px);border-color:var(--accent);box-shadow:0 22px 36px rgba(0,0,0,.25);background-color:color-mix(in srgb,var(--surface) 96%,var(--accent) 4%)}
  .mode-card:nth-child(2):hover {transform:translateY(-14px) translateZ(16px)}
  .mode-index {color:var(--accent);font:800 .7rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em}
  .mode-name {margin-top:13px;color:var(--muted);font-size:.75rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
  .mode-value {margin-top:7px;font-size:1.25rem;line-height:1.25}
  .mode-duration {margin-top:4px;font-size:.9rem;color:var(--ink)}
  .mode-card p {margin:12px 0 0;color:var(--muted);font-size:.78rem;line-height:1.55}
  .mode-state {margin-top:auto;padding-top:14px;color:var(--accent);font-size:.7rem;font-weight:800}
  .hud-page .section--key_fact {border-radius:var(--hud-radius-xl) 12px var(--hud-radius-md) 12px;background:color-mix(in srgb,var(--surface) 92%,var(--accent) 8%)}
  .hud-page .section--key_fact .section-body {display:grid;gap:18px}
  .hud-page .structured--metrics {border:0}
  .metric-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
  .metric-grid .structured-title {grid-column:1 / -1;margin:0;padding:0 0 7px}
  .metric-card {position:relative;display:flex;flex-direction:column;min-height:148px;padding:17px 16px 15px;border:1px solid var(--line);border-radius:var(--hud-radius-md);background:color-mix(in srgb,var(--surface) 86%,transparent);box-shadow:0 14px 28px rgba(0,0,0,.14);transition:transform .25s ease,border-color .25s ease,background-color .25s ease}
  .metric-card:nth-of-type(3n) {border-radius:8px var(--hud-radius-lg) 8px var(--hud-radius-md)}
  .metric-card:hover {transform:translateY(-6px);border-color:var(--accent);background-color:color-mix(in srgb,var(--surface) 96%,var(--accent) 4%)}
  .metric-label {color:var(--muted);font-size:.72rem;line-height:1.4}
  .metric-value {margin-top:auto;color:var(--ink);font:700 clamp(2rem,4vw,3.1rem)/1 Georgia,'Noto Serif Arabic',serif;letter-spacing:-.055em;direction:ltr;text-align:start}
  .metric-context {margin-top:5px;color:var(--accent);font-size:.76rem;line-height:1.45;min-height:1.4em}
  .hud-page .section--key_fact .structured--facts {margin:0;grid-template-columns:repeat(2,minmax(0,1fr));padding:14px 18px;border:1px solid var(--line);border-radius:12px;background:color-mix(in srgb,var(--surface) 72%,transparent)}
  .hud-page .section--key_fact .structured--facts .structured-title {grid-column:1 / -1}
  .hud-page .section--timeline {grid-template-columns:minmax(190px,.58fr) minmax(0,1.42fr);border-radius:12px var(--hud-radius-xl) var(--hud-radius-xl) 12px;background:radial-gradient(circle at 100% 0,color-mix(in srgb,var(--accent) 12%,transparent),transparent 35%),color-mix(in srgb,var(--surface) 92%,var(--bg));border-color:color-mix(in srgb,var(--accent) 42%,var(--line))}
  .hud-page .section--timeline .section-heading h2 {font-size:clamp(1.6rem,2.8vw,2.6rem)}
  .structured--timeline {height:100%}
  .timeline-track {position:relative;padding:3px 0 3px 12px}
  .timeline-track .structured-title {margin:0 0 13px}
  .timeline-track ol {list-style:none;margin:0;padding:0}
  .timeline-step {position:relative;display:grid;grid-template-columns:50px minmax(0,1fr);gap:16px;min-height:76px;padding:0 0 18px}
  .timeline-step:not(:last-child)::after {content:"";position:absolute;top:37px;bottom:0;inset-inline-start:24px;width:1px;background:linear-gradient(var(--accent),var(--line))}
  .timeline-marker {position:relative;z-index:1;display:grid;place-items:center;width:36px;height:36px;border:1px solid var(--accent);border-radius:50%;background:var(--surface);box-shadow:0 0 0 5px color-mix(in srgb,var(--accent) 8%,transparent)}
  .timeline-marker span {color:var(--accent);font:800 .68rem/1 ui-monospace,SFMono-Regular,Menlo,monospace}
  .timeline-step--blocked .timeline-marker {border-color:#d68c5e;box-shadow:0 0 0 5px rgba(214,140,94,.1)}
  .timeline-step--blocked .status-indicator {color:#d68c5e}
  .timeline-step--passed .timeline-marker {border-color:var(--accent);box-shadow:0 0 0 5px color-mix(in srgb,var(--accent) 10%,transparent),0 0 22px color-mix(in srgb,var(--accent) 20%,transparent)}
  .timeline-step--passed .status-indicator {color:var(--accent)}
  .timeline-topline {display:flex;justify-content:space-between;gap:16px;align-items:baseline}
  .timeline-topline strong {font-size:1rem;line-height:1.4}
  .status-indicator {color:var(--accent);font-size:.72rem;font-weight:800;white-space:nowrap}
  .timeline-content p {margin:5px 0 0;color:var(--muted);font-size:.84rem;line-height:1.6}
  .hud-page .section--identity {border-radius:var(--hud-radius-xl) 8px 8px var(--hud-radius-xl)}
  .hud-page .section--operations {grid-template-columns:minmax(0,1.22fr) minmax(180px,.78fr);border-radius:8px var(--hud-radius-xl) 8px var(--hud-radius-xl);background:color-mix(in srgb,var(--surface) 94%,var(--accent) 6%)}
  .hud-page .section--operations .section-heading {order:2;align-self:center;padding-inline-start:16px;border-inline-start:2px solid var(--accent)}
  .hud-page .section--operations .section-body {order:1}
  .hud-page .section--content {grid-template-columns:minmax(210px,.8fr) minmax(0,1.2fr);border-radius:var(--hud-radius-md) var(--hud-radius-xl) var(--hud-radius-md) var(--hud-radius-xl)}
  .hud-page .section--content {display:block}
  .hud-page .section--content .section-heading {display:flex;align-items:baseline;justify-content:space-between;gap:24px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid var(--line)}
  .hud-page .section--content .section-heading h2 {margin:0;max-width:none}
  .hud-page .section--content .section-body {max-width:980px;margin-inline-start:auto}
  .hud-page .section--release {border-inline-start:4px solid var(--accent);border-radius:10px var(--hud-radius-xl) var(--hud-radius-xl) 10px;background:color-mix(in srgb,var(--soft) 62%,var(--surface))}
  .hud-footer {display:flex;align-items:center;gap:12px;padding:28px 4px 34px;color:var(--muted);font-size:.76rem;border-top:1px solid var(--line)}
  .footer-mark {display:grid;place-items:center;width:28px;height:28px;color:var(--accent);border:1px solid var(--accent);border-radius:50%;font:700 1rem/1 Georgia,serif}
  .footer-note {margin-inline-start:auto;color:var(--muted);font-size:.7rem}
}
@media screen and (max-width:820px) {
  .hud-topbar {align-items:flex-start;flex-direction:column;gap:8px;margin-top:10px}
  .hud-topbar-meta {width:100%;justify-content:space-between}
  .hud-page .hero {padding-top:12px}
  .hero-surface {padding:22px 18px;border-radius:var(--hud-radius-lg)}
  .hud-page .hero-meta {margin-bottom:28px}
  .hud-page .hero-grid {display:block}
  .hud-page h1 {font-size:clamp(2.45rem,11vw,4rem);max-width:15ch}
  .hud-page .summary-note {margin-top:26px}
  .hud-metrics {grid-template-columns:1fr 1fr}
  .hud-metrics-label {grid-column:1 / -1}
  .hud-signal {min-height:82px}
  .hud-page .section {display:block;margin-bottom:16px;padding:20px 18px;border-radius:var(--hud-radius-lg)}
  .hud-page .section-heading {margin-bottom:18px}
  .hud-page .section--verdict .section-heading h2 {font-size:2rem}
  .hud-page .section--sequence .section-heading {margin-bottom:14px}
  .mode-grid {grid-template-columns:1fr}
  .mode-card:nth-child(2) {transform:none}
  .mode-card:nth-child(2):hover {transform:translateY(-8px)}
  .metric-grid {grid-template-columns:repeat(2,minmax(0,1fr))}
  .metric-card {min-height:132px}
  .metric-value {font-size:2.35rem}
  .verdict-row {grid-template-columns:1fr;gap:5px}
  .timeline-topline {display:block}
  .status-indicator {display:block;margin-top:4px}
  .hud-footer {align-items:flex-start;flex-wrap:wrap}
  .footer-note {width:100%;margin-inline-start:40px}
}
@media print {
  .omega-preloader {display:none !important}
  .hud-page::before {display:none}
  .hud-topbar {position:static;margin:0 0 5mm;box-shadow:none;border-radius:0;background:#fff;color:#444;backdrop-filter:none;animation:none}
  .hero-surface {padding:5mm;border-radius:0;box-shadow:none;background:#fff;perspective:none;transform:none;animation:none}
  .hero-surface::after {display:none}
  .hud-signal {border-radius:0;box-shadow:none;background:#fff}
}
'''


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
    hud_labels = HUD_LABELS["ar" if lang == "ar" else "en"]
    hud_signals = hud_signal_tiles(bundle, lang)
    hud_profile = HUD_PROFILE_LABELS.get(profile, profile.upper())
    landing_surface = kind == "audit"
    public_status = "حالة موثقة" if lang == "ar" else "Evidence-led"
    public_signal_label = "لمحة من الدليل" if lang == "ar" else "Evidence at a glance"
    if landing_surface:
        hud_topbar = (
            f'<div class="hud-topbar"><div class="hud-brand"><span>Ω OMEGA</span>'
            f'<small>{esc(hud_profile)} · {esc(hud_labels["surface"])}</small></div>'
            f'<div class="hud-topbar-meta"><span class="hud-status">{esc(public_status)}</span></div></div>'
        )
    else:
        hud_topbar = (
            f'<div class="hud-topbar"><div class="hud-brand"><span>Ω OMEGA</span>'
            f'<small>{esc(hud_profile)} · {esc(hud_labels["surface"])}</small></div>'
            f'<div class="hud-topbar-meta"><span class="hud-status">{esc(hud_labels["signals"])}</span>'
            f'<span>{len(truth.get("sources", []))} {esc(hud_labels["sources"])}</span>'
            f'<span>{len(truth.get("claims", []))} {esc(hud_labels["claims"])}</span></div></div>'
        )
    visual_treatments = {
        "decision": "verdict",
        "effort": "mode-snapshot",
        "facts": "metrics",
        "timeline": "timeline",
        "identity": "matrix",
        "operations": "matrix",
        "content": "matrix",
        "release": "matrix",
    }
    baseline = next((claim.get("value", "") for claim in truth.get("claims", []) if claim.get("claim_id") == "AHS.FACT.BASELINE_HOURS"), "")
    sections = []
    for section in composition["sections"]:
        section_intent = section["presentation_intent"]
        section_label = labels.get(section_intent, section_intent)
        copy_html = "".join(render_copy(blocks[ref], section_intent) for ref in section.get("copy_refs", []) if ref in blocks and blocks[ref].get("role") not in {"headline", "subheadline"})
        structured_html = "".join(render_structured(block, lang, section["section_id"], baseline) for block in section.get("structured_blocks", []))
        treatment = visual_treatments.get(section["section_id"], section_intent)
        attrs = f'id="{esc(section["section_id"])}" data-section-id="{esc(section["section_id"])}" data-presentation-intent="{esc(section_intent)}" data-visual-treatment="{esc(treatment)}"'
        sections.append(f'<section class="section section--{esc(section_intent)}" {attrs}><div class="section-heading"><div class="section-kicker">{esc(section_label)}</div><h2>{esc(section["purpose"])}</h2></div><div class="section-body">{copy_html}{structured_html}</div></section>')
    footer = "AHS · قراءة تنفيذية مستقلة" if lang == "ar" else ("AHS · independent operational review" if intent == "audit_report" else "Omega · independent decision brief")
    css = stylesheet(theme).replace('html[data-surface-profile="omega-hud"],html[data-surface-profile="aion"]', ":root").replace('html[data-surface-profile="omega-hud"],html[data-surface-profile="aion"],html[data-surface-profile="omega-gold"],html[data-surface-profile="omega-teal"],html[data-surface-profile="omega-cyan"]', ":root")
    css += hud_stylesheet_overrides()
    css += '''
@media screen {
  html {scroll-behavior:smooth}
  .hud-page .section {scroll-margin-top:104px}
  .landing-hero {padding-top:clamp(18px,3vw,34px)}
  .landing-hero .hero-surface {min-height:clamp(520px,63vh,720px);display:flex;flex-direction:column;justify-content:space-between;padding:clamp(30px,5vw,68px);border-radius:36px 36px 14px 36px;background:radial-gradient(circle at 88% 12%,color-mix(in srgb,var(--accent) 18%,transparent),transparent 31%),linear-gradient(145deg,color-mix(in srgb,var(--surface) 95%,var(--bg)),var(--surface));box-shadow:0 30px 90px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.045)}
  .landing-hero .hero-grid {align-items:center;gap:clamp(34px,8vw,126px)}
  .landing-hero .hero-copy {max-width:920px}
  .landing-hero h1 {font-size:clamp(3rem,7.3vw,6.6rem);max-width:11ch;letter-spacing:-.06em}
  .landing-hero .lede {max-width:58ch;font-size:clamp(1rem,1.3vw,1.18rem);line-height:1.9}
  .hero-cta {display:inline-flex;align-items:center;gap:12px;margin-top:clamp(26px,4vw,42px);padding:12px 18px 12px 20px;border:1px solid color-mix(in srgb,var(--accent) 68%,var(--line));border-radius:999px;color:var(--ink);background:linear-gradient(110deg,color-mix(in srgb,var(--accent) 19%,var(--surface)),color-mix(in srgb,var(--surface) 88%,transparent));box-shadow:0 12px 28px rgba(0,0,0,.2),0 0 30px color-mix(in srgb,var(--accent) 10%,transparent);font-size:.82rem;font-weight:900;text-decoration:none;transition:transform .25s ease,background-color .25s ease,border-color .25s ease,box-shadow .25s ease}
  .hero-cta span {display:grid;place-items:center;width:25px;height:25px;border:1px solid var(--accent);border-radius:50%;color:var(--accent);font-size:1rem;line-height:1;transition:transform .25s ease}
  .hero-cta:hover,.hero-cta:focus-visible {transform:translateY(-4px);border-color:var(--accent);background:color-mix(in srgb,var(--accent) 19%,var(--surface));box-shadow:0 18px 34px rgba(0,0,0,.28),0 0 38px color-mix(in srgb,var(--accent) 15%,transparent)}
  .hero-cta:hover span,.hero-cta:focus-visible span {transform:translate(3px,-2px)}
  .hero-cta:focus-visible {outline:2px solid var(--accent);outline-offset:4px}
  .landing-hero .hud-metrics {margin-top:clamp(34px,5vw,66px)}
  .hud-page .section--key_fact {border-radius:14px 34px 14px 34px;background:linear-gradient(125deg,color-mix(in srgb,var(--surface) 95%,var(--accent) 5%),var(--surface))}
  .hud-page .section--timeline {border-radius:34px 14px 34px 14px;padding-block:clamp(28px,4vw,44px);background:radial-gradient(circle at 4% 50%,color-mix(in srgb,var(--accent) 13%,transparent),transparent 30%),color-mix(in srgb,var(--surface) 92%,var(--bg))}
  .hud-page .section--evidence_matrix:nth-of-type(4) {border-radius:14px 34px 14px 14px}
  .hud-page .section--evidence_matrix:nth-of-type(5) {border-radius:34px 14px 14px 34px;background:color-mix(in srgb,var(--surface) 94%,var(--accent) 6%)}
  .hud-page .section--evidence_matrix:nth-of-type(6) {border-radius:14px 14px 34px 14px}
  .hud-page .section--evidence_matrix:nth-of-type(7) {border-radius:14px 34px 34px 14px}
  .hud-page .section--timeline .timeline-step {transition:transform .25s ease}
  .hud-page .section--timeline .timeline-step:hover {transform:translateX(-4px)}
}
@media screen and (max-width:820px) {
  .landing-hero .hero-surface {min-height:0;padding:26px 20px;border-radius:26px 26px 12px 26px}
  .landing-hero h1 {font-size:clamp(2.7rem,12vw,4.5rem);max-width:12ch}
  .landing-hero .lede {line-height:1.8}
  .hero-cta {margin-top:26px}
  .hud-page .section--timeline,.hud-page .section--evidence_matrix {border-radius:var(--hud-radius-lg)}
}
'''
    css += '\n@media screen{.hero-grid{margin-top:clamp(28px,4vw,52px)}h1{font-size:clamp(2.45rem,5.2vw,4.6rem);max-width:21ch}.document-grid--proposal .section-heading,.document-grid--proposal .section-body{padding-block:clamp(28px,4vw,48px)}.document-grid--proposal .section-heading h2{font-size:clamp(1.35rem,2vw,2rem)} } @media screen and (max-width:820px){h1{font-size:clamp(2.1rem,10vw,3.35rem);max-width:19ch}.hero{padding-bottom:32px} } @media print{.document-grid{display:block}.section{display:grid;grid-template-columns:28% 1fr;gap:10%;break-inside:avoid}.section-heading,.section-body{grid-column:auto;grid-row:auto} }'
    favicon = favicon_data_uri(theme)
    preloader = preloader_markup()
    hero_cta = ""
    if landing_surface:
        cta_label = "استعرض مسار الإغلاق" if lang == "ar" else "Review closure path"
        hero_cta = f'<a class="hero-cta" href="#timeline">{esc(cta_label)}<span aria-hidden="true">↗</span></a>'
    page_mode = "landing" if landing_surface else "document"
    return f'''<!doctype html><html lang="{esc(lang)}" dir="{esc(direction)}" data-surface-profile="{esc(profile)}" data-document-intent="{esc(intent)}" data-document-kind="{esc(kind)}" data-page-mode="{page_mode}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="omega:surface" content="screen"><meta name="omega:brand_profile" content="omega-default"><meta name="omega:page_size" content="viewport"><meta name="omega:page_intent" content="screen_first"><meta name="omega:theme_profile" content="{esc(profile)}"><meta name="omega:language" content="{esc(lang)}"><meta name="omega:direction" content="{esc(direction)}"><meta name="omega:source_count" content="{len(truth.get("sources", []))}"><meta name="omega:claim_count" content="{len(truth.get("claims", []))}"><link rel="icon" href="data:image/svg+xml;base64,{favicon}" type="image/svg+xml"><title>{esc(title)}</title><style>{css}</style></head><body>{preloader}<div class="page hud-page">{hud_topbar}<header class="hero hero--{esc(kind)}{' landing-hero' if landing_surface else ''}"><div class="hero-surface"><div class="hero-meta"><span class="brandmark">Ω OMEGA</span><span class="document-label">{esc(DOC_LABELS.get("ar" if lang == "ar" else "en", {}).get(intent, "Omega document"))}</span></div><div class="hero-grid"><div class="hero-copy"><h1 {hero_attrs}>{hero_trace}{esc(title)}</h1><p class="lede" {sub_attrs}>{sub_trace}{esc(subheadline.get("text", "") if subheadline else "")}</p>{hero_cta}</div>{note}</div><div class="hud-metrics"><div class="hud-metrics-label">{esc(public_signal_label if landing_surface else hud_labels["signals"])}</div>{hud_signals}</div></div></header><main class="document-grid document-grid--{esc(kind)}">{"".join(sections)}</main><footer class="hud-footer"><span class="footer-mark">Ω</span><span>{esc(footer)}</span><span class="footer-note">{esc("قرار مبني على ما أمكن إثباته" if lang == "ar" else "Decision built on what can be proven")}</span></footer></div></body></html>'''


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
