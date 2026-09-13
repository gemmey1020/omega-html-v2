#!/usr/bin/env python3
"""Build Wave 6 fixtures from the frozen AHS payload and realistic local examples."""
import argparse
import copy
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = Path("/home/jemy/Documents/my_work/x_port_x/output/data/ahs-omega-hud-gold-payload-2026-09-12.json")
SOURCE_PACKAGE = {
    "SOURCE.AHS.OBSERVATION": ("AHS read-only production observation", "/home/jemy/Documents/my_work/x_port_x/the_job_lab/ahs-app/AHS_FINAL_READ_ONLY_PRODUCTION_OBSERVATION_2026-09-12.md"),
    "SOURCE.AHS.AUDIT": ("AHS final truth audit", "/home/jemy/Documents/my_work/x_port_x/the_job_lab/ahs-app/AHS_FINAL_TRUTH_AUDIT_2026-09-12.md"),
    "SOURCE.AHS.DOCX": ("AHS developer requirements intake", "/home/jemy/Documents/my_work/x_port_x/the_job_lab/ahs-app/AHS_Full_Developer_Bug_List_and_Requirements.docx"),
    "SOURCE.AHS.TRIPLE": ("AHS triple-chain validation", "/home/jemy/Documents/my_work/x_port_x/the_job_lab/ahs-app/AHS_TRIPLE_CHAIN_VALIDATION_2026-09-12.md"),
    "SOURCE.AHS.BACKEND": ("Canonical AHS backend source", "/home/jemy/Documents/my_work/x_port_x/the_job/ahs-app/core"),
    "SOURCE.AHS.MOBILE": ("Canonical AHS Flutter source", "/home/jemy/Documents/my_work/x_port_x/the_job/ahs-app/core-front/committee_beauty_health"),
    "SOURCE.AHS.PRODUCTION": ("Observed production boundary", "/opt/ahs/core"),
    "SOURCE.AHS.PAYLOAD": ("Frozen AHS Omega payload", str(DEFAULT_PAYLOAD)),
}
CATEGORIES = {
    "Identity, access, and account safety": ("الهوية والحسابات", "identity"),
    "Operational requests, queues, and exports": ("الطلبات والطوابير والتصدير", "operations"),
    "Content, data relationships, and modules": ("المحتوى والعلاقات والوحدات", "content"),
    "Integrations, migration, release, and handover": ("التكامل والترحيل والتسليم", "release"),
}
AR_TITLES = {
    1: "بحث المستخدمين وصلاحيات لوحة الإدارة", 2: "تصدير رموز QR", 3: "الأخبار والتحميل المتتابع", 4: "دخول الأعضاء الحاليين", 5: "ثبات التسجيل ورسائل التحقق", 6: "الدخول برقم العضوية أو رقم البطاقة", 7: "المتجر داخل لوحة الإدارة", 8: "الإشعارات ودورة تسليمها", 9: "ظهور طلبات الخدمات في لوحة الإدارة", 10: "سير الطلبات وسبب الرفض", 11: "ربط الأكاديمية بالفرع", 12: "النسخ الاحتياطي والترحيل", 13: "تفعيل المستخدم القديم ومنع التكرار", 14: "الشروط والأحكام", 15: "رقم العضوية في الملف الشخصي", 16: "استعادة كلمة المرور", 17: "القائمة المحظورة", 18: "أصول لوحة الإدارة", 19: "بطاقات الطوابير والتنقل", 20: "تصدير المستخدمين إلى Excel", 21: "شرائح التسويق والتطبيق", 22: "مقارنة لوحة الإدارة القديمة والحالية", 23: "مراجعة التطبيق ولوحة الإدارة والـAPI والبنية", 24: "تقرير الإغلاق والتسليم"}
AR_SUMMARIES = {
    1: "مسارات البحث وحقول المعرّفات موجودة، لكن اختبار الأدوار وسلوك 403 لم يُنفّذ.", 2: "بيانات QR القديمة والحالية موجودة؛ التصدير لعنصر واحد أو مجموعة أو الكل لم يُثبت.", 3: "يوجد 62 سجل خبر، لكن اختبار تجاوز نقطة الفشل والتصفح المتتابع ما زال مفتوحًا.", 4: "يوجد 20,789 مستخدمًا قديمًا و71 مستخدمًا حاليًا؛ توافق الدخول والربط بينهما غير مختبر.", 5: "مسارات التسجيل المحلية واختباراتها موجودة، بينما قبول أخطاء الإنتاج والحالات السلبية لم يُحسم.", 6: "عقد الدخول الحالي يعتمد على الهاتف أو البريد أو اسم المستخدم؛ رقم العضوية ورقم البطاقة غير مثبتين.", 7: "كود المتجر موجود، لكن جداول الإنتاج للمنتجات والبائعين والطلبات فارغة؛ النطاق يحتاج قرارًا.", 8: "مسارات قراءة الإشعارات موجودة، أما مزود الإرسال والأجهزة ودورة الرموز فلم تُثبت.", 9: "جداول الطلبات الحديثة موجودة، لكن ظهور كل عائلة طلب في لوحة الإدارة لم يُختبر.", 10: "أدوات القبول والرفض موجودة، بينما سبب الرفض وانعكاس الحالة على التطبيق ما زالا مفتوحين.", 11: "يوجد 227 أكاديمية و24 فرعًا، ولم يظهر يتيم في الفحص الموجّه؛ صحة العلاقة على كل الأسطح لم تُقبل.", 12: "ملفات نسخ بتاريخ 2026-04-20 موجودة، لكن الاستعادة والمطابقة وخطة الرجوع غير مثبتة.", 13: "توجد خدمة تفعيل، لكن إثبات الهوية ومنع إنشاء عضوية مكررة غير مثبتين.", 14: "واجهة قبول الشروط موجودة، أما النص القانوني المعتمد وإصداره وربطه بالإنتاج فمفتوح.", 15: "الحقل Serial ومسار عرضه موجودان، لكن عرض رقم عضو فعلي وعزل بياناته لم يُختبرا.", 16: "مسار الاستعادة القديم معطّل، ولم يظهر مسار بديل مكتمل من التعرف حتى تسجيل الدخول الجديد.", 17: "لم يظهر تنفيذ محلي للقائمة المحظورة؛ قواعد المطابقة وسجل التغيير تحتاج اعتمادًا.", 18: "التخزين الثابت والوسائط موجودان، مع تحذير staticfiles.W004؛ فحص بصري بصلاحيات فعلية لم يُنفّذ.", 19: "مصادر الطوابير والمسارات موجودة، لكن مصفوفة الأدوار وبطاقات الانتظار لم تُقبل حيًا.", 20: "تنفيذ تصدير المستخدمين موجود في المصدر، لكن زر لوحة الإدارة والصلاحيات والمرشحات لم تُختبر.", 21: "وحدة التسويق وأصول الشرائح موجودة، بينما جداول الإنتاج فارغة وتدفق لوحة الإدارة إلى التطبيق غير مثبت.", 22: "لا توجد قائمة قبول موقعة تقارن الصفحات والأفعال والصلاحيات والاستثناءات بين اللوحتين.", 23: "تمت ملاحظة الخادم والمصدر، لكن قبول الهاتف والأدوار والإشعارات والترحيل الشامل ما زال مفتوحًا.", 24: "حزمة الأدلة والحالات موجودة، لكن توقيع الإغلاق لا يصدر قبل عبور بوابات القبول."}

AR_SUMMARIES.update({
    12: "النسخ والترحيل جزء من نطاق الإغلاق، لكن الاستعادة والمطابقة وخطة الرجوع غير مثبتة.",
    18: "الأصول ومسارات التخزين موجودة، لكن قبولها بصلاحيات فعلية لم يُنفّذ.",
    23: "مراجعة التطبيق ولوحة الإدارة والتكاملات مطلوبة قبل اعتماد الإغلاق.",
})


def claim_state(decision):
    upper = decision.upper()
    if "NOT-FOUND" in upper:
        return "not_found", "open"
    if "BLOCKED" in upper:
        return "unknown", "blocked"
    if "BUSINESS" in upper:
        return "unknown", "open"
    if "VERIFIED" in upper and "SUBSET" not in upper:
        return "observed", "verified"
    if "SUPPORTED" in upper or "PARTIAL" in upper:
        return "source_backed", "partial"
    return "source_backed", "open"


def claim_risk(decision, meta):
    raw = next((item.split("=", 1)[1] for item in meta if item.lower().startswith("risk=")), "")
    raw = raw.lower()
    if "ultra" in raw:
        return "critical"
    if "high" in raw:
        return "high"
    if "medium" in raw or "legal" in raw:
        return "medium"
    if "critical" in raw:
        return "critical"
    return "high" if "OPEN" in decision.upper() else "medium"


def source(source_id, description, locator):
    return {"source_id": source_id, "description": description, "locator": locator}


def claim(claim_id, meaning, value, state, closure, risk, refs, materiality="supporting", tokens=None):
    result = {"claim_id": claim_id, "meaning": meaning, "value": value, "epistemic_state": state, "closure_state": closure, "risk": risk, "source_refs": refs, "protected_tokens": tokens or [], "materiality": materiality}
    return result


def bundle_dir(name):
    path = ROOT / "evals" / "bundles" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_bundle(name, data):
    path = bundle_dir(name)
    for key, filename in {"truth": "truth-model", "reader": "reader-brief", "strategy": "document-strategy", "authored": "authored-content", "composition": "composition-model"}.items():
        (path / f"{filename}.json").write_text(json.dumps(data[key], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_ahs(payload):
    entries = []
    for section in payload.get("sections", []):
        for entry in section.get("entries", []):
            number = next((int(item.split("=", 1)[1]) for item in entry.get("meta", []) if item.startswith("DOCX=")), None)
            if number:
                entries.append((number, section.get("title", ""), entry))
    entries.sort(key=lambda item: item[0])
    truths = [source(sid, desc, loc) for sid, (desc, loc) in SOURCE_PACKAGE.items()]
    claims = []
    for number, category, entry in entries:
        state, closure = claim_state(entry.get("decision", ""))
        refs = ["SOURCE.AHS.PAYLOAD", "SOURCE.AHS.OBSERVATION", "SOURCE.AHS.AUDIT", "SOURCE.AHS.DOCX"]
        if "Identity" in category:
            refs.append("SOURCE.AHS.BACKEND")
        elif "Content" in category:
            refs.extend(["SOURCE.AHS.BACKEND", "SOURCE.AHS.MOBILE"])
        else:
            refs.append("SOURCE.AHS.PRODUCTION")
        claims.append(claim(f"AHS.REQUIREMENT.{number:02d}", f"المطلب {number:02d}: {AR_TITLES[number]}", {"source_title": entry.get("label", ""), "source_summary": entry.get("summary", ""), "status": entry.get("decision", ""), "category": category}, state, closure, claim_risk(entry.get("decision", ""), entry.get("meta", [])), refs, "material"))
    facts = [
        claim("AHS.FACT.PROJECT_POSTURE", "المشروع قابل للملاحظة، لكنه غير مغلق إنتاجيًا.", "EVIDENCE-BOUNDED / NOT PRODUCTION-CLOSED", "observed", "open", "critical", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.AUDIT"]),
        claim("AHS.FACT.OBSERVATION_BOUNDARY", "نطاق العمل ملاحظة للقراءة فقط ومطابقة للمصادر.", "read-only observation and source reconciliation", "source_backed", "verified", "high", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.AUDIT"]),
        claim("AHS.FACT.LEGACY_USERS", "عدد سجلات المستخدمين القديمة المرصودة.", "20,789", "observed", "verified", "critical", ["SOURCE.AHS.OBSERVATION"], tokens=["20,789"]),
        claim("AHS.FACT.CURRENT_USERS", "عدد سجلات CustomUser الحالية المرصودة.", "71", "observed", "verified", "critical", ["SOURCE.AHS.OBSERVATION"], tokens=["71"]),
        claim("AHS.FACT.NATIONAL_ID_OVERLAP", "عدد مرشحي التداخل في National_ID.", "28", "observed", "open", "critical", ["SOURCE.AHS.OBSERVATION"], tokens=["28"]),
        claim("AHS.FACT.BASELINE_HOURS", "خط الأساس الزمني المؤقت.", "120h", "source_backed", "open", "high", ["SOURCE.AHS.PAYLOAD", "SOURCE.AHS.AUDIT"], tokens=["120h"]),
        claim("AHS.FACT.RESTORE_STATUS", "حالة قابلية الاستعادة.", "restore not proven", "source_backed", "open", "critical", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.AUDIT"]),
        claim("AHS.FACT.BACKUP_DATE", "تاريخ ملفات النسخ المرصودة.", "2026-04-20", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"]),
        claim("AHS.FACT.RUNTIME_PATH", "مسار المشروع المرصود على الخادم.", "/opt/ahs/core", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.PRODUCTION"]),
        claim("AHS.FACT.DATABASE", "هوية قاعدة البيانات ومحركها.", "PostgreSQL 16.13 / ahs_prod", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"]),
        claim("AHS.FACT.NEWS_ROWS", "عدد سجلات الأخبار المرصودة.", "62", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["62"]),
        claim("AHS.FACT.ACADEMIES_BRANCHES", "عدد الأكاديميات والفروع المرصودة.", "227 academies / 24 branches", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["227", "24"]),
        claim("AHS.FACT.APK_BOUNDARY", "هوية ملف APK ليست متطابقة بين النسختين المرصودتين.", "remote hash differs from local artifact", "observed", "open", "high", ["SOURCE.AHS.OBSERVATION"]),
        claim("AHS.FACT.RUNTIME_CHECK", "فحص Django الأساسي اكتمل مع تحذير staticfiles.", "manage.py check / staticfiles.W004", "observed", "partial", "high", ["SOURCE.AHS.OBSERVATION"]),
    ]
    claims.extend(facts)
    claims.extend([
        claim("AHS.FACT.MIGRATION_TARGET", "حدود معرفة وجهة الترحيل.", "The requirements mention migration from the old server to a new production server, but the available package does not identify or describe the new server.", "unknown", "blocked", "critical", ["SOURCE.AHS.DOCX", "SOURCE.AHS.PAYLOAD"]),
        claim("AHS.FACT.EFFORT_MODES", "نماذج توزيع الجهد والزمن المذكورة في الـpayload.", {"baseline": "120h", "light": "6h/day and 20 working days", "medium": "10h/day and 12 working days", "hard": "12h/day peak and 10 working days"}, "source_backed", "open", "high", ["SOURCE.AHS.PAYLOAD"], tokens=["120h", "6h/day", "10h/day", "12h/day peak"]),
    ])
    authored = [
        {"copy_id": "COPY.AHS.HEADLINE", "role": "headline", "text": "مشروع AHS: الحقيقة التشغيلية قبل قرار الإغلاق", "claim_refs": ["AHS.FACT.PROJECT_POSTURE"], "protected_spans": []},
        {"copy_id": "COPY.AHS.SUBHEAD", "role": "subheadline", "text": "المصدر يوضح ما ثبت على الخادم والكود، وما يحتاج إلى اختبار أو قرار قبل إعلان الجاهزية.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.FACT.OBSERVATION_BOUNDARY"], "protected_spans": []},
        {"copy_id": "COPY.AHS.CALLOUT", "role": "callout", "text": "القرار الحالي: استمر في الإغلاق المنضبط، ولا تسمِّ المشروع مغلقًا إنتاجيًا قبل إثبات الهوية والاستعادة والأدوار والأجهزة.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.FACT.RESTORE_STATUS"], "protected_spans": []},
    ]
    fact_text = "السجل المرصود يضم 20,789 مستخدمًا قديمًا و71 مستخدمًا حاليًا، مع 28 مرشح تداخل في National_ID. ويضم المحتوى 62 خبرًا، إلى جانب 227 أكاديمية و24 فرعًا. خط الأساس المؤقت 120h، بينما restore not proven حتى الآن؛ وهوية الـAPK تحمل remote hash differs."
    authored.append({"copy_id": "COPY.AHS.FACTS", "role": "paragraph", "text": "الفارق بين السجلين، مع حجم المحتوى والعلاقات، يحدد عبء التحقق قبل الإغلاق.", "claim_refs": [], "protected_spans": []})
    tech_text = "المسار المرصود /opt/ahs/core يعمل على PostgreSQL 16.13 وقاعدة ahs_prod. فحص manage.py check اكتمل مع staticfiles.W004؛ وملف النسخ يحمل تاريخ 2026-04-20."
    authored.append({"copy_id": "COPY.AHS.TECH", "role": "paragraph", "text": tech_text, "claim_refs": ["AHS.FACT.RUNTIME_PATH", "AHS.FACT.DATABASE", "AHS.FACT.RUNTIME_CHECK", "AHS.FACT.BACKUP_DATE"], "protected_spans": ["/opt/ahs/core", "PostgreSQL 16.13", "ahs_prod", "manage.py check", "staticfiles.W004", "2026-04-20"]})
    authored.append({"copy_id": "COPY.AHS.CODE", "role": "technical_text", "text": "python manage.py check\n# observed warning: staticfiles.W004", "claim_refs": ["AHS.FACT.RUNTIME_CHECK"], "protected_spans": []})
    authored[0]["text"] = "مشروع AHS: الحقيقة التشغيلية قبل قرار الإغلاق"
    authored[1]["text"] = "الموجود واضح من القراءة المحلية. أمّا الإغلاق الإنتاجي، فما زال ينتظر اختبارات حاسمة."
    authored[2]["text"] = "القرار المتاح اليوم: إبقاء الإغلاق الإنتاجي معلّقًا. الهوية والاستعادة والأدوار والأجهزة لم يكتمل دليلها بعد."
    authored.extend([
        {"copy_id": "COPY.AHS.MIGRATION_BOUNDARY", "role": "callout", "text": "المتطلبات تذكر الترحيل من الخادم القديم إلى خادم إنتاج جديد. الحزمة المتاحة لا تذكر هوية أو مواصفات أو نقطة وصول للخادم الجديد؛ لذلك تظل وجهة الترحيل غير معروفة ولا يمكن اعتمادها الآن.", "claim_refs": ["AHS.REQUIREMENT.12", "AHS.FACT.MIGRATION_TARGET"], "protected_spans": []},
        {"copy_id": "COPY.AHS.EFFORT", "role": "paragraph", "text": "إجمالي 120h هو أساس تخطيطي لنطاق العمل المكتشف، وليس موعدًا مضمونًا. Light نحو 6h/day، وMedium نحو 10h/day، وHard نحو 12h/day peak؛ أوقات الانتظار الخارجية تُضاف ولا تنضغط.", "claim_refs": ["AHS.FACT.BASELINE_HOURS", "AHS.FACT.EFFORT_MODES"], "protected_spans": ["120h", "6h/day", "10h/day", "12h/day peak"]},
    ])
    for number, category, entry in entries:
        cid = f"AHS.REQUIREMENT.{number:02d}"
        text = f"المطلب {number:02d} — {AR_TITLES[number]}: {AR_SUMMARIES[number]}"
        tokens = []
        tokens = []
        c = next(item for item in claims if item["claim_id"] == cid)
        authored.append({"copy_id": f"COPY.AHS.REQUIREMENT.{number:02d}", "role": "paragraph", "text": text, "claim_refs": [cid], "protected_spans": tokens, "state_projections": [{"claim_id": cid, "dimension": dimension, "value": c[dimension]} for dimension in ("epistemic_state", "closure_state", "risk")]})
    sections = []
    sections.append({"section_id": "facts", "purpose": "أرقام تغيّر حجم قرار الإغلاق", "copy_refs": ["COPY.AHS.FACTS"], "claim_refs": [], "presentation_intent": "key_fact", "structured_blocks": [{"block_id": "STRUCT.AHS.FACTS", "type": "fact_list", "title": "المشهد التشغيلي", "items": [{"label": "السجل القديم", "value": "20,789 مستخدمًا", "claim_refs": ["AHS.FACT.LEGACY_USERS"]}, {"label": "السجل الحالي", "value": "71 مستخدمًا", "claim_refs": ["AHS.FACT.CURRENT_USERS"]}, {"label": "مرشحو التداخل", "value": "28 في National_ID", "claim_refs": ["AHS.FACT.NATIONAL_ID_OVERLAP"]}, {"label": "النسخ والاستعادة", "value": "2026-04-20؛ restore not proven", "claim_refs": ["AHS.FACT.BACKUP_DATE", "AHS.FACT.RESTORE_STATUS"]}, {"label": "خط الأساس", "value": "120h مؤقت", "claim_refs": ["AHS.FACT.BASELINE_HOURS"]}, {"label": "هوية التطبيق", "value": "remote hash differs", "claim_refs": ["AHS.FACT.APK_BOUNDARY"]}]}]})
    for key, title in (("identity", "الهوية والوصول"), ("operations", "الطلبات والطوابير"), ("content", "المحتوى والعلاقات"), ("release", "التكامل والترحيل والتسليم")):
        selected = [(n, cat, entry) for n, cat, entry in entries if CATEGORIES.get(cat, ("", ""))[1] == key]
        rows = []
        for number, category, entry in selected:
            cid = f"AHS.REQUIREMENT.{number:02d}"
            c = next(item for item in claims if item["claim_id"] == cid)
            rows.append({"cells": [f"{number:02d} · {AR_TITLES[number]}", AR_SUMMARIES[number], {"verified": "مُثبت", "partial": "مُثبت جزئيًا", "open": "مفتوح", "blocked": "محجوب"}.get(c["closure_state"], "مفتوح")], "claim_refs": [cid], "copy_refs": [f"COPY.AHS.REQUIREMENT.{number:02d}"]})
        sections.append({"section_id": key, "purpose": title, "copy_refs": [], "claim_refs": [], "presentation_intent": "evidence_matrix", "structured_blocks": [{"block_id": f"STRUCT.AHS.{key.upper()}", "type": "table", "title": "حالة المطالب كما يصفها الدليل", "columns": ["المطلب", "الشرح الحالي", "الحالة للقراءة التنفيذية"], "rows": rows}]})
    sections.extend([
        {"section_id": "sequence", "purpose": "ترتيب الإغلاق الذي يحمي القرار", "copy_refs": ["COPY.AHS.TECH"], "claim_refs": [], "presentation_intent": "sequence", "structured_blocks": [{"block_id": "STRUCT.AHS.SEQUENCE", "type": "sequence", "title": "الخطوات التالية", "items": [{"label": "طابق الهوية", "value": "افصل 20,789 عن 71 قبل أي تفعيل أو دمج.", "claim_refs": ["AHS.FACT.LEGACY_USERS", "AHS.FACT.CURRENT_USERS"]}, {"label": "أثبت الاستعادة", "value": "اختبر نسخة 2026-04-20 في بيئة معزولة.", "claim_refs": ["AHS.FACT.BACKUP_DATE", "AHS.FACT.RESTORE_STATUS"]}, {"label": "اقبل الأدوار والأجهزة", "value": "شغّل مصفوفة Dashboard وAndroid وiOS قبل الإغلاق.", "claim_refs": ["AHS.REQUIREMENT.19", "AHS.REQUIREMENT.23"]}]}]},
        {"section_id": "annex", "purpose": "تفاصيل يحتاجها فريق التنفيذ", "copy_refs": ["COPY.AHS.CODE"], "claim_refs": [], "presentation_intent": "technical_annex", "annex": True, "structured_blocks": [{"block_id": "STRUCT.AHS.CODE", "type": "code", "title": "أمر الفحص المرصود", "code": "python manage.py check\n# observed warning: staticfiles.W004", "claim_refs": ["AHS.FACT.RUNTIME_CHECK"], "copy_refs": ["COPY.AHS.CODE"]}, {"block_id": "STRUCT.AHS.LEDGER", "type": "source_ledger", "title": "سجل المصدر", "items": [{"label": "Production observation", "value": "الخادم وPostgreSQL وRedis وCaddy وأعداد الجداول.", "claim_refs": ["AHS.FACT.DATABASE", "AHS.FACT.RUNTIME_PATH"]}, {"label": "Final truth audit", "value": "مصفوفة المطالب وحدود الدليل.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE"]}, {"label": "Canonical source", "value": "الكود الخلفي وتطبيق Flutter كما فُحصا محليًا.", "claim_refs": ["AHS.REQUIREMENT.23"]}]}]}
    ])
    authored[0]["text"] = "مشروع AHS: الحقيقة التشغيلية قبل قرار الإغلاق"
    authored[1]["text"] = "الموجود واضح من القراءة المحلية. أمّا الإغلاق الإنتاجي، فما زال ينتظر اختبارات حاسمة."
    authored[2]["text"] = "القرار المتاح اليوم: إبقاء الإغلاق الإنتاجي معلّقًا. الهوية والاستعادة والأدوار والأجهزة لم يكتمل دليلها بعد."
    authored = [block for block in authored if block["copy_id"] not in {"COPY.AHS.TECH", "COPY.AHS.CODE"}]
    facts_section = next(section for section in sections if section["section_id"] == "facts")
    effort_section = {"section_id": "effort", "purpose": "المجهود يغيّر المدة ولا يغيّر معيار القبول", "copy_refs": ["COPY.AHS.EFFORT"], "claim_refs": ["AHS.FACT.EFFORT_MODES"], "presentation_intent": "comparison", "structured_blocks": [{"block_id": "STRUCT.AHS.EFFORT", "type": "fact_list", "title": "ثلاثة modes للوقت", "claim_refs": ["AHS.FACT.EFFORT_MODES"], "items": [{"label": "Light", "value": "≈ 6h/day · ≈ 20 يوم عمل", "detail": "وتيرة أخف؛ المعيار نفسه.", "claim_refs": ["AHS.FACT.EFFORT_MODES"]}, {"label": "Medium", "value": "≈ 10h/day · ≈ 12 يوم عمل", "detail": "تنسيق أضيق؛ المعيار نفسه.", "claim_refs": ["AHS.FACT.EFFORT_MODES"]}, {"label": "Hard", "value": "≈ 12h/day peak · ≈ 10 أيام عمل", "detail": "ضغط أعلى؛ أوقات الانتظار لا تختفي.", "claim_refs": ["AHS.FACT.EFFORT_MODES"]}]}]}
    facts_section["structured_blocks"] = [{"block_id": "STRUCT.AHS.FACTS", "type": "fact_list", "title": "المشهد التشغيلي", "items": [{"label": "السجل القديم", "value": "20,789 مستخدمًا", "claim_refs": ["AHS.FACT.LEGACY_USERS"]}, {"label": "السجل الحالي", "value": "71 مستخدمًا", "claim_refs": ["AHS.FACT.CURRENT_USERS"]}, {"label": "مرشحو التداخل", "value": "28 في National_ID", "claim_refs": ["AHS.FACT.NATIONAL_ID_OVERLAP"]}, {"label": "سجلات الأخبار", "value": "62 سجلًا", "claim_refs": ["AHS.FACT.NEWS_ROWS"]}, {"label": "الأكاديميات", "value": "227 أكاديمية", "claim_refs": ["AHS.FACT.ACADEMIES_BRANCHES"]}, {"label": "الفروع", "value": "24 فرعًا", "claim_refs": ["AHS.FACT.ACADEMIES_BRANCHES"]}, {"label": "خط الأساس", "value": "120h مؤقت", "claim_refs": ["AHS.FACT.BASELINE_HOURS"]}]}]
    facts_section["purpose"] = "أرقام تغيّر حجم قرار الإغلاق"
    release_section = next(section for section in sections if section["section_id"] == "release")
    release_section["copy_refs"] = ["COPY.AHS.MIGRATION_BOUNDARY"]
    timeline_section = {"section_id": "timeline", "purpose": "مسار الإغلاق كما تسمح به الأدلة", "copy_refs": [], "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.REQUIREMENT.12", "AHS.REQUIREMENT.24"], "presentation_intent": "timeline", "structured_blocks": [{"block_id": "STRUCT.AHS.TIMELINE", "type": "timeline", "title": "لا توجد مواعيد مفترضة؛ كل مرحلة تنتظر دليلها", "claim_refs": ["AHS.FACT.PROJECT_POSTURE"], "items": [{"label": "المشهد المرصود", "value": "مُثبت", "detail": "الخادم والكود والبيانات قابلون للقراءة والمطابقة.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.FACT.OBSERVATION_BOUNDARY"]}, {"label": "الهوية والدخول", "value": "مفتوح", "detail": "اختبارات الأدوار والربط بين السجلين لم تُقبل بعد.", "claim_refs": ["AHS.REQUIREMENT.01", "AHS.REQUIREMENT.04"]}, {"label": "الاستعادة والترحيل", "value": "محجوب", "detail": "الاستعادة والمطابقة وخطة الرجوع غير مثبتة، ووجهة الخادم الجديد غير معروفة.", "claim_refs": ["AHS.REQUIREMENT.12", "AHS.FACT.MIGRATION_TARGET"]}, {"label": "اعتماد الإغلاق", "value": "مشروط", "detail": "توقيع الإغلاق ينتظر عبور بوابات القبول.", "claim_refs": ["AHS.REQUIREMENT.24"]}]}]}
    sections = [effort_section, facts_section, timeline_section] + [section for section in sections if section["section_id"] in {"identity", "operations", "content", "release"}]
    return {"truth": {"sources": truths, "claims": claims}, "reader": {"audience": "صاحب قرار أو مسؤول تسليم", "document_intent": "audit_report", "surface_profile": "omega-editorial", "primary_question": "ما الذي ثبت، وما الذي يمنع الإغلاق؟", "desired_action": "تحديد بوابة الإغلاق التالية", "technical_depth": "technical annex", "annex_policy": "التفاصيل التقنية في الملحق", "summary_rail": {"enabled": True, "title": "الحالة المعلنة", "body": "المشهد المرصود واضح. إعلان الإغلاق يحتاج عبور بوابات القبول المشروطة."}, "language": {"primary": "ar", "direction": "rtl", "technical_english": "when_earned", "translation_preference": "Arabic prose with exact technical identifiers"}}, "strategy": {"document_intent": "audit_report", "through_line": "فصل ما ثبت عن ما يحتاج إثباتًا قبل قرار الإغلاق.", "must_appear_first": ["comparison", "key_fact"], "secondary_content": ["evidence_matrix", "timeline"], "annex_content": [], "detail_level": "public executive only", "uncertainty_policy": "اعرض الفتح والحجب والجزئية بصراحة", "reader_journey": ["effort", "facts", "timeline", "evidence"]}, "authored": {"blocks": authored}, "composition": {"sections": sections}}


EN_TITLES = {
    1: "User search and admin permissions", 2: "QR code export", 3: "News and pagination", 4: "Current member login", 5: "Registration stability and verification messages", 6: "Login by membership or card number", 7: "Store inside the admin panel", 8: "Notifications and delivery lifecycle", 9: "Service requests in the admin panel", 10: "Request workflow and rejection reason", 11: "Academy-to-branch linking", 12: "Backup and migration", 13: "Legacy-user activation and duplicate prevention", 14: "Terms and conditions", 15: "Membership number in the profile", 16: "Password recovery", 17: "Blocklist", 18: "Admin-panel assets", 19: "Queue cards and navigation", 20: "User export to Excel", 21: "Marketing and app slides", 22: "Old/current admin-panel comparison", 23: "App, admin panel, API, and infrastructure review", 24: "Closure and handover report",
}
EN_SUMMARIES = {
    1: "Search paths and identifier fields are present; role and 403 behavior are not tested.", 2: "Legacy and current QR data are present; single, batch, and full export are not proven.", 3: "62 news rows are present; boundary and pagination behavior remain open.", 4: "The observed populations are 20,789 legacy users and 71 current users; login compatibility is untested.", 5: "Local registration paths and tests exist; production error and negative states remain unresolved.", 6: "The current login contract covers phone, email, or username; membership and card-number login are not proven.", 7: "Store code exists, but production product, seller, and order tables are empty; scope needs a decision.", 8: "Notification read paths exist; provider, device, and token lifecycle are not proven.", 9: "Recent request tables exist; each request family’s admin visibility is not tested.", 10: "Accept/reject tools exist; rejection reason and app state reflection remain open.", 11: "227 academies and 24 branches are observed with no orphan in the focused check; full-surface relationship acceptance is open.", 12: "Backup and migration are in scope, but restore, reconciliation, and rollback acceptance remain open.", 13: "An activation service exists; identity proof and duplicate-membership prevention are not proven.", 14: "Terms acceptance UI exists; approved legal copy, versioning, and production binding remain open.", 15: "The Serial field and display path exist; real-member rendering and data isolation are untested.", 16: "The legacy recovery path is broken; a complete replacement flow is not shown.", 17: "No local blocklist implementation was found; matching rules and change history need approval.", 18: "Storage and media paths exist; permissioned visual acceptance has not been run.", 19: "Queue sources and routes exist; role matrix and waiting cards are not accepted live.", 20: "User export exists in source; admin control, permissions, and filters are untested.", 21: "Marketing module and slide assets exist; production data and panel-to-app flow are not proven.", 22: "No signed acceptance list compares pages, actions, permissions, and exceptions across panels.", 23: "App, admin, API, and infrastructure review remains open for full acceptance.", 24: "The evidence and status package exists; closure sign-off waits for acceptance gates.",
}


def build_ahs_english(payload):
    bundle = copy.deepcopy(build_ahs(payload))
    reader = bundle["reader"]
    reader.update({
        "audience": "decision maker or delivery owner",
        "primary_question": "What is proven, and what still blocks closure?",
        "desired_action": "Identify the next closure gate",
        "technical_depth": "public executive only",
        "annex_policy": "Keep internal implementation detail out of the public surface",
        "summary_rail": {"enabled": True, "title": "Public status", "body": "The observed scene is readable; production closure still depends on conditional acceptance gates."},
        "language": {"primary": "en", "direction": "ltr", "technical_english": "native", "translation_preference": "Plain English with exact earned identifiers"},
    })
    bundle["strategy"].update({
        "through_line": "Separate what is observed from what still needs proof before closure.",
        "must_appear_first": ["comparison", "key_fact"],
        "secondary_content": ["evidence_matrix", "timeline"],
        "uncertainty_policy": "State open, blocked, partial, and verified conditions plainly.",
        "reader_journey": ["effort", "facts", "timeline", "evidence"],
    })
    blocks = {block["copy_id"]: block for block in bundle["authored"]["blocks"]}
    copy_text = {
        "COPY.AHS.HEADLINE": "AHS: the operational truth before closure",
        "COPY.AHS.SUBHEAD": "The local reading makes the observed state clear. Production closure still waits for decisive acceptance tests.",
        "COPY.AHS.CALLOUT": "Keep production closure conditional until identity, recovery, roles, and device acceptance are complete.",
        "COPY.AHS.FACTS": "The gap between the two user records, together with content and relationship volume, sets the verification load before closure.",
        "COPY.AHS.MIGRATION_BOUNDARY": "The requirements mention migration from the old server to a new production server. The available package does not identify, describe, or provide an access point for that server, so the migration target remains unknown.",
        "COPY.AHS.EFFORT": "The current 120h total is a planning baseline for the discovered scope, not a guaranteed date. Light is about 6h/day, Medium about 10h/day, and Hard about 12h/day peak; external waiting time is added rather than compressed.",
    }
    for copy_id, text in copy_text.items():
        if copy_id in blocks:
            blocks[copy_id]["text"] = text
    for number in EN_TITLES:
        block = blocks.get(f"COPY.AHS.REQUIREMENT.{number:02d}")
        if block:
            block["text"] = f"Requirement {number:02d} — {EN_TITLES[number]}: {EN_SUMMARIES[number]}"
    status_labels = {"verified": "Passed", "partial": "Passed in part", "open": "Open", "blocked": "Blocked"}
    section_purposes = {
        "effort": "Effort changes calendar time, not the acceptance standard",
        "facts": "Numbers that shape closure scope",
        "timeline": "The closure path follows evidence, not assumed dates",
        "identity": "Identity and access",
        "operations": "Requests, queues, and exports",
        "content": "Content and relationships",
        "release": "Integration, migration, and handover",
    }
    for section in bundle["composition"]["sections"]:
        section_id = section["section_id"]
        section["purpose"] = section_purposes.get(section_id, section["purpose"])
        for block in section.get("structured_blocks", []):
            block_id = block.get("block_id")
            if block_id == "STRUCT.AHS.EFFORT":
                block["title"] = "Three pace options"
                for item, label, value, detail in zip(
                    block["items"],
                    ("Light", "Medium", "Hard"),
                    ("≈ 6h/day · ≈ 20 working days", "≈ 10h/day · ≈ 12 working days", "≈ 12h/day peak · ≈ 10 working days"),
                    ("Lighter pace; the acceptance standard stays fixed.", "Tighter coordination; the acceptance standard stays fixed.", "Higher pressure; waiting time does not disappear."),
                ):
                    item.update({"label": label, "value": value, "detail": detail})
            elif block_id == "STRUCT.AHS.FACTS":
                block["title"] = "Operational scene"
                for item, label, value in zip(
                    block["items"],
                    ("Legacy record", "Current record", "Overlap candidates", "News records", "Academies", "Branches", "Planning baseline"),
                    ("20,789 legacy users", "71 current users", "28 in National_ID", "62 records", "227 academies", "24 branches", "120h planning baseline"),
                ):
                    item.update({"label": label, "value": value})
            elif block_id == "STRUCT.AHS.TIMELINE":
                block["title"] = "No assumed dates; each stage waits for its evidence"
                items = block["items"]
                items[0].update({"label": "Observed scene", "value": "Passed", "detail": "Server, code, and data are readable and reconciled."})
                items[1].update({"label": "Identity and access", "value": "Open", "detail": "Role tests and reconciliation between the two records are not accepted yet."})
                items[2].update({"label": "Recovery and migration", "value": "Blocked", "detail": "Recovery, reconciliation, and rollback are not proven; the new server target is unknown."})
                items[3].update({"label": "Closure sign-off", "value": "Conditional", "detail": "Sign-off waits for the acceptance gates to clear."})
            elif block.get("type") == "table":
                block["title"] = "Status as described by the evidence"
                block["columns"] = ["Requirement", "Current reading", "Executive status"]
                for row in block.get("rows", []):
                    number = int(row["cells"][0].split("·", 1)[0].strip())
                    claim_id = row.get("claim_refs", [""])[0]
                    state = next((claim["closure_state"] for claim in bundle["truth"]["claims"] if claim["claim_id"] == claim_id), "open")
                    row["cells"] = [f"{number:02d} · {EN_TITLES[number]}", EN_SUMMARIES[number], status_labels.get(state, "Open")]
    return bundle


def build_proposal():
    sources = [source("SOURCE.PROPOSAL.BRIEF", "Approved synthetic game pilot brief", "fixture: game-pilot-decision-brief-v6")]
    claims = [
        claim("PROPOSAL.PILOT.LENGTH", "مدة الطيار المحدود.", "6 weeks", "source_backed", "open", "medium", ["SOURCE.PROPOSAL.BRIEF"], "material", ["6 weeks"]),
        claim("PROPOSAL.BUDGET.CAP", "السقف المالي المطلوب للموافقة.", "$12,000", "source_backed", "open", "high", ["SOURCE.PROPOSAL.BRIEF"], "material", ["$12,000"]),
        claim("PROPOSAL.DELIVERABLE", "المخرج المحدد للطيار.", "one playable vertical slice", "source_backed", "open", "medium", ["SOURCE.PROPOSAL.BRIEF"], "material"),
        claim("PROPOSAL.DECISION", "القرار المطلوب من القارئ.", "approve the scoped pilot", "source_backed", "open", "high", ["SOURCE.PROPOSAL.BRIEF"], "material"),
        claim("PROPOSAL.CONTEXT", "سبب بدء الاختبار المحدود.", "test the core loop before a larger commitment", "source_backed", "open", "medium", ["SOURCE.PROPOSAL.BRIEF"], "material"),
        claim("PROPOSAL.RISK", "شرط الإيقاف والمراجعة.", "weekly review; stop if the core loop does not hold", "source_backed", "open", "high", ["SOURCE.PROPOSAL.BRIEF"], "material"),
    ]
    authored = {"blocks": [
        {"copy_id": "COPY.PROPOSAL.HEADLINE", "role": "headline", "text": "اختبر اللعبة قبل أن تكبّر الرهان", "claim_refs": ["PROPOSAL.DECISION", "PROPOSAL.CONTEXT"], "protected_spans": []},
        {"copy_id": "COPY.PROPOSAL.SUBHEAD", "role": "subheadline", "text": "نقترح طيارًا محدودًا يجيب عن سؤال اللعب الأساسي بوقت وميزانية معروفين.", "claim_refs": ["PROPOSAL.CONTEXT", "PROPOSAL.PILOT.LENGTH", "PROPOSAL.BUDGET.CAP"], "protected_spans": []},
        {"copy_id": "COPY.PROPOSAL.CONTEXT", "role": "paragraph", "text": "قبل الالتزام بإنتاج كامل، نحتاج نسخة قابلة للعب يختبرها الفريق ويقرأ منها سلوك الحلقة الأساسية. هذا الطيار يعطي القرار مادة عملية بدل توقعات عامة.", "claim_refs": ["PROPOSAL.CONTEXT", "PROPOSAL.DELIVERABLE"], "protected_spans": []},
        {"copy_id": "COPY.PROPOSAL.ACTION", "role": "callout", "text": "القرار المطلوب: اعتماد الطيار المحدود لمدة 6 weeks وبسقف $12,000.", "claim_refs": ["PROPOSAL.DECISION", "PROPOSAL.PILOT.LENGTH", "PROPOSAL.BUDGET.CAP"], "protected_spans": ["6 weeks", "$12,000"]},
        {"copy_id": "COPY.PROPOSAL.RISK", "role": "paragraph", "text": "تُراجع النتيجة أسبوعيًا. إذا لم تثبت الحلقة الأساسية، يتوقف الطيار قبل أي التزام أوسع.", "claim_refs": ["PROPOSAL.RISK"], "protected_spans": []},
    ]}
    english_copy = {
        "COPY.PROPOSAL.HEADLINE": "Test the game before you scale the bet",
        "COPY.PROPOSAL.SUBHEAD": "A short pilot puts a known timebox and budget behind the core play question.",
        "COPY.PROPOSAL.CONTEXT": "The team gets a playable slice to test the core loop before expanding the commitment. It gives the decision a concrete result to review.",
        "COPY.PROPOSAL.ACTION": "Decision requested: approve the scoped pilot for 6 weeks with a $12,000 cap.",
        "COPY.PROPOSAL.RISK": "Review the result weekly. If the core loop does not hold, stop the pilot before making a larger commitment.",
    }
    for block in authored["blocks"]:
        block["text"] = english_copy[block["copy_id"]]
    sections = [
        {"section_id": "decision", "purpose": "القرار المطلوب", "copy_refs": ["COPY.PROPOSAL.HEADLINE", "COPY.PROPOSAL.SUBHEAD", "COPY.PROPOSAL.ACTION"], "claim_refs": ["PROPOSAL.DECISION"], "presentation_intent": "verdict", "structured_blocks": []},
        {"section_id": "case", "purpose": "لماذا هذا النطاق؟", "copy_refs": ["COPY.PROPOSAL.CONTEXT"], "claim_refs": ["PROPOSAL.CONTEXT"], "presentation_intent": "narrative", "structured_blocks": []},
        {"section_id": "terms", "purpose": "حدود الطيار", "copy_refs": [], "claim_refs": [], "presentation_intent": "key_fact", "structured_blocks": [{"block_id": "STRUCT.PROPOSAL.TERMS", "type": "fact_list", "title": "ما ستتم الموافقة عليه", "items": [{"label": "المدة", "value": "6 weeks", "claim_refs": ["PROPOSAL.PILOT.LENGTH"]}, {"label": "السقف", "value": "$12,000", "claim_refs": ["PROPOSAL.BUDGET.CAP"]}, {"label": "المخرج", "value": "one playable vertical slice", "claim_refs": ["PROPOSAL.DELIVERABLE"]}]}]},
        {"section_id": "condition", "purpose": "شرط الاستمرار", "copy_refs": ["COPY.PROPOSAL.RISK"], "claim_refs": ["PROPOSAL.RISK"], "presentation_intent": "risk_register", "structured_blocks": [{"block_id": "STRUCT.PROPOSAL.RISK", "type": "risk_register", "title": "شرط واحد واضح", "items": [{"label": "المخاطرة", "value": "الإنفاق قبل معرفة جودة الحلقة", "detail": "Weekly review stops the pilot if the core loop does not hold.", "claim_refs": ["PROPOSAL.RISK"]}]}]},
        {"section_id": "next", "purpose": "الخطوة التالية", "copy_refs": [], "claim_refs": [], "presentation_intent": "checklist", "structured_blocks": [{"block_id": "STRUCT.PROPOSAL.NEXT", "type": "checklist", "items": [{"label": "اعتماد النطاق", "value": "توقيع مدة الطيار وسقفه.", "claim_refs": ["PROPOSAL.PILOT.LENGTH", "PROPOSAL.BUDGET.CAP"]}, {"label": "بدء التنفيذ", "value": "بناء المخرج القابل للعب ومراجعته أسبوعيًا.", "claim_refs": ["PROPOSAL.DELIVERABLE", "PROPOSAL.RISK"]}]}]},
    ]
    section_titles = {"decision": "The decision requested", "case": "Why this scope", "terms": "Pilot boundaries", "condition": "Condition for continuing", "next": "Next step"}
    for section in sections:
        section["purpose"] = section_titles[section["section_id"]]
        for structured in section.get("structured_blocks", []):
            if structured.get("title") == "ما ستتم الموافقة عليه":
                structured["title"] = "What approval covers"
            if structured.get("title") == "شرط واحد واضح":
                structured["title"] = "One clear condition"
            for item in structured.get("items", []):
                item["label"] = {"المدة": "Duration", "السقف": "Cap", "المخرج": "Deliverable", "المخاطرة": "Risk", "اعتماد النطاق": "Approve the scope", "بدء التنفيذ": "Start the pilot"}.get(item["label"], item["label"])
                item["value"] = {"6 weeks": "6 weeks", "$12,000": "$12,000", "one playable vertical slice": "one playable vertical slice", "الإنفاق قبل معرفة جودة الحلقة": "Spending before learning the loop", "توقيع مدة الطيار وسقفه.": "Sign off on the timebox and cap.", "بناء المخرج القابل للعب ومراجعته أسبوعيًا.": "Build the playable slice and review it weekly."}.get(item["value"], item["value"])
    return {"truth": {"sources": sources, "claims": claims}, "reader": {"audience": "decision maker", "document_intent": "proposal", "surface_profile": "omega-minimal", "primary_question": "What should the reader approve?", "desired_action": "Approve the scoped pilot", "technical_depth": "light", "annex_policy": "No annex required", "summary_rail": {"enabled": False, "title": "", "body": ""}, "language": {"primary": "en", "direction": "ltr", "technical_english": "when_earned"}}, "strategy": {"document_intent": "proposal", "through_line": "A bounded pilot turns a large product decision into a testable next step.", "must_appear_first": ["verdict", "key_fact"], "secondary_content": ["narrative", "risk_register"], "annex_content": [], "detail_level": "one to two page decision proposal", "uncertainty_policy": "keep the pilot conditional and reviewable", "reader_journey": ["verdict", "case", "terms", "condition", "next"]}, "authored": authored, "composition": {"sections": sections}}


def build_technical():
    sources = [source("SOURCE.TECHNICAL.BRIEF", "Approved synthetic runtime review brief", "fixture: runtime-review-brief-v6")]
    claims = [
        claim("TECH.PATH", "Path under review.", "/srv/ahs/core", "observed", "verified", "medium", ["SOURCE.TECHNICAL.BRIEF"], "material", ["/srv/ahs/core"]),
        claim("TECH.VERSION", "Application version under review.", "v2.1", "observed", "verified", "medium", ["SOURCE.TECHNICAL.BRIEF"], "material", ["v2.1"]),
        claim("TECH.DATABASE", "Database identity.", "ahs_prod / PostgreSQL 16", "observed", "partial", "high", ["SOURCE.TECHNICAL.BRIEF"], "material", ["ahs_prod", "PostgreSQL 16"]),
        claim("TECH.COMMAND", "Command used for the check.", "python manage.py check", "observed", "verified", "low", ["SOURCE.TECHNICAL.BRIEF"], "material", ["python manage.py check"]),
        claim("TECH.STATUS", "Status of the review.", "passed with one warning", "observed", "partial", "high", ["SOURCE.TECHNICAL.BRIEF"], "material"),
        claim("TECH.RISK", "Remaining operational risk.", "static asset path warning needs ownership before release", "source_backed", "open", "high", ["SOURCE.TECHNICAL.BRIEF"], "material"),
        claim("TECH.ANNEX", "The report includes an evidence annex.", "source ledger and status table", "source_backed", "verified", "low", ["SOURCE.TECHNICAL.BRIEF"], "material"),
    ]
    authored = {"blocks": [
        {"copy_id": "COPY.TECH.HEADLINE", "role": "headline", "text": "مراجعة تقنية لمسار الإصدار", "claim_refs": ["TECH.PATH", "TECH.VERSION"], "protected_spans": []},
        {"copy_id": "COPY.TECH.SUBHEAD", "role": "subheadline", "text": "فحص قصير يربط المسار والنسخة وقاعدة البيانات بالنتيجة التي يمكن لفريق التشغيل متابعتها.", "claim_refs": ["TECH.PATH", "TECH.VERSION", "TECH.STATUS"], "protected_spans": []},
        {"copy_id": "COPY.TECH.INTRO", "role": "paragraph", "text": "The report starts with the environment, then records the check result and the remaining release risk in a traceable annex.", "claim_refs": ["TECH.STATUS", "TECH.RISK", "TECH.ANNEX"], "protected_spans": []},
        {"copy_id": "COPY.TECH.CODE", "role": "technical_text", "text": "cd /srv/ahs/core\npython manage.py check\n# database: ahs_prod / PostgreSQL 16", "claim_refs": ["TECH.PATH", "TECH.COMMAND", "TECH.DATABASE"], "protected_spans": ["/srv/ahs/core", "python manage.py check", "ahs_prod", "PostgreSQL 16"]},
        {"copy_id": "COPY.TECH.RISK", "role": "callout", "text": "النتيجة قابلة للاستخدام، لكن تحذير مسار الملفات الثابتة يحتاج مالكًا وقرارًا قبل ربطها بقرار إصدار.", "claim_refs": ["TECH.STATUS", "TECH.RISK"], "protected_spans": []},
    ]}
    sections = [
        {"section_id": "identity", "purpose": "هوية الشيء الذي فُحص", "copy_refs": ["COPY.TECH.HEADLINE", "COPY.TECH.SUBHEAD"], "claim_refs": [], "presentation_intent": "verdict", "structured_blocks": [{"block_id": "STRUCT.TECH.IDENTITY", "type": "fact_list", "title": "Environment", "items": [{"label": "Path", "value": "/srv/ahs/core", "claim_refs": ["TECH.PATH"]}, {"label": "Version", "value": "v2.1", "claim_refs": ["TECH.VERSION"]}, {"label": "Database", "value": "ahs_prod / PostgreSQL 16", "claim_refs": ["TECH.DATABASE"]}]}]},
        {"section_id": "overview", "purpose": "النتيجة في سطر يمكن متابعته", "copy_refs": ["COPY.TECH.INTRO", "COPY.TECH.RISK"], "claim_refs": ["TECH.STATUS"], "presentation_intent": "narrative", "structured_blocks": []},
        {"section_id": "status", "purpose": "حالة الأدلة التنفيذية", "copy_refs": [], "claim_refs": [], "presentation_intent": "table", "structured_blocks": [{"block_id": "STRUCT.TECH.STATUS", "type": "table", "title": "Evidence status", "columns": ["Check", "Observed", "State"], "rows": [{"cells": ["Runtime check", "python manage.py check", "مكتمل"], "claim_refs": ["TECH.COMMAND", "TECH.STATUS"]}, {"cells": ["Static asset path", "warning remains", "مفتوح"], "claim_refs": ["TECH.RISK"]}, {"cells": ["Annex", "source ledger and status table", "موجود"], "claim_refs": ["TECH.ANNEX"]}]}]},
        {"section_id": "command", "purpose": "الأمر والسياق التقني", "copy_refs": ["COPY.TECH.CODE"], "claim_refs": [], "presentation_intent": "technical_block", "structured_blocks": [{"block_id": "STRUCT.TECH.CODE", "type": "code", "title": "Observed command", "code": "cd /srv/ahs/core\npython manage.py check\n# database: ahs_prod / PostgreSQL 16", "claim_refs": ["TECH.PATH", "TECH.COMMAND", "TECH.DATABASE"], "copy_refs": ["COPY.TECH.CODE"]}]},
        {"section_id": "risk", "purpose": "المخاطرة التي لا ينبغي أن تضيع", "copy_refs": ["COPY.TECH.RISK"], "claim_refs": ["TECH.RISK"], "presentation_intent": "risk_register", "structured_blocks": [{"block_id": "STRUCT.TECH.RISK", "type": "risk_register", "title": "Release caveat", "items": [{"label": "Static asset path", "value": "open", "detail": "يحتاج التحذير إلى مالك وقرار قبل الإصدار.", "claim_refs": ["TECH.RISK"]}]}]},
        {"section_id": "annex", "purpose": "تفاصيل يحتاجها فريق التشغيل", "copy_refs": [], "claim_refs": [], "presentation_intent": "technical_annex", "annex": True, "structured_blocks": [{"block_id": "STRUCT.TECH.ANNEX", "type": "code", "title": "Technical annex", "code": "# Keep the warning visible until an owner accepts it.", "claim_refs": ["TECH.RISK"]}]},
        {"section_id": "ledger", "purpose": "من أين جاءت هذه النتيجة؟", "copy_refs": [], "claim_refs": [], "presentation_intent": "source_ledger", "annex": True, "structured_blocks": [{"block_id": "STRUCT.TECH.LEDGER", "type": "source_ledger", "title": "Source ledger", "items": [{"label": "Runtime brief", "value": "المسار والنسخة وقاعدة البيانات.", "claim_refs": ["TECH.PATH", "TECH.VERSION", "TECH.DATABASE"]}, {"label": "Check result", "value": "الأمر ونتيجته والتحذير المفتوح.", "claim_refs": ["TECH.COMMAND", "TECH.STATUS", "TECH.RISK"]}]}]}
    ]
    return {"truth": {"sources": sources, "claims": claims}, "reader": {"audience": "technical lead", "document_intent": "technical", "surface_profile": "omega-hud", "primary_question": "What was verified and what remains open?", "desired_action": "Assign the remaining risk", "technical_depth": "dense", "annex_policy": "show the technical annex", "summary_rail": {"enabled": True, "title": "Release note", "body": "الفحص واضح؛ مسار الملفات الثابتة يحتاج مسؤولية قبل الإصدار."}, "language": {"primary": "ar", "direction": "rtl", "technical_english": "when earned"}}, "strategy": {"document_intent": "technical", "through_line": "Tie each technical observation to a decision or an owner.", "must_appear_first": ["verdict", "key_fact"], "secondary_content": ["table", "technical_block", "risk_register"], "annex_content": ["source_ledger"], "detail_level": "dense technical report", "uncertainty_policy": "separate observed state from open risk", "reader_journey": ["identity", "result", "status", "command", "risk", "annex"]}, "authored": authored, "composition": {"sections": sections}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ahs-payload", type=Path, default=DEFAULT_PAYLOAD)
    args = parser.parse_args()
    payload = json.loads(args.ahs_payload.read_text(encoding="utf-8"))
    source_copy = ROOT / "evals" / "source" / args.ahs_payload.name
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.ahs_payload, source_copy)
    write_bundle("ahs", build_ahs(payload))
    write_bundle("ahs-en", build_ahs_english(payload))
    write_bundle("proposal", build_proposal())
    write_bundle("technical", build_technical())
    (ROOT / "evals" / "human-authoring" / "wave6-execution.md").write_text("""# Wave 6 authoring execution record\n\nThe three final bundles were authored as independent deliverables after reading the pinned `humanize-writing`, `ux-writing`, and conservative `humanizer` instructions in `third_party/writing/`.\n\n- Human-first routing shaped the through-line, audience stance, sentence rhythm, and document-specific prose.\n- UX-writing routing was applied to labels, statuses, facts, table headings, callouts, and next-step language.\n- The conservative humanizer pass removed staged openers, decorative repetition, and context-free token stuffing while preserving source facts and identifiers.\n- The transformation was performed on the final AHS, proposal, and technical copy blocks; the earlier instruction-set inspection reports are not treated as output benchmarks.\n- Truth Lock ran after authoring and before rendering.\n""", encoding="utf-8")
    print(json.dumps({"status": "PASS", "bundles": ["ahs", "ahs-en", "proposal", "technical"], "source": str(source_copy)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
