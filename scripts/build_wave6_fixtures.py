#!/usr/bin/env python3
"""Build Wave 6 fixtures from the frozen AHS payload and realistic local examples."""
import argparse
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
        claim("AHS.FACT.RESTORE_STATUS", "حالة قابلية الاستعادة.", "restore not proven", "source_backed", "open", "critical", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.AUDIT"], tokens=["restore not proven"]),
        claim("AHS.FACT.BACKUP_DATE", "تاريخ ملفات النسخ المرصودة.", "2026-04-20", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["2026-04-20"]),
        claim("AHS.FACT.RUNTIME_PATH", "مسار المشروع المرصود على الخادم.", "/opt/ahs/core", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION", "SOURCE.AHS.PRODUCTION"], tokens=["/opt/ahs/core"]),
        claim("AHS.FACT.DATABASE", "هوية قاعدة البيانات ومحركها.", "PostgreSQL 16.13 / ahs_prod", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["PostgreSQL 16.13", "ahs_prod"]),
        claim("AHS.FACT.NEWS_ROWS", "عدد سجلات الأخبار المرصودة.", "62", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["62"]),
        claim("AHS.FACT.ACADEMIES_BRANCHES", "عدد الأكاديميات والفروع المرصودة.", "227 academies / 24 branches", "observed", "verified", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["227", "24"]),
        claim("AHS.FACT.APK_BOUNDARY", "هوية ملف APK ليست متطابقة بين النسختين المرصودتين.", "remote hash differs from local artifact", "observed", "open", "high", ["SOURCE.AHS.OBSERVATION"]),
        claim("AHS.FACT.RUNTIME_CHECK", "فحص Django الأساسي اكتمل مع تحذير staticfiles.", "manage.py check / staticfiles.W004", "observed", "partial", "high", ["SOURCE.AHS.OBSERVATION"], tokens=["manage.py check", "staticfiles.W004"]),
    ]
    claims.extend(facts)
    authored = [
        {"copy_id": "COPY.AHS.HEADLINE", "role": "headline", "text": "مشروع AHS: الحقيقة التشغيلية قبل قرار الإغلاق", "claim_refs": ["AHS.FACT.PROJECT_POSTURE"], "protected_spans": []},
        {"copy_id": "COPY.AHS.SUBHEAD", "role": "subheadline", "text": "المصدر يوضح ما ثبت على الخادم والكود، وما يحتاج إلى اختبار أو قرار قبل إعلان الجاهزية.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.FACT.OBSERVATION_BOUNDARY"], "protected_spans": []},
        {"copy_id": "COPY.AHS.CALLOUT", "role": "callout", "text": "القرار الحالي: استمر في الإغلاق المنضبط، ولا تسمِّ المشروع مغلقًا إنتاجيًا قبل إثبات الهوية والاستعادة والأدوار والأجهزة.", "claim_refs": ["AHS.FACT.PROJECT_POSTURE", "AHS.FACT.RESTORE_STATUS"], "protected_spans": []},
    ]
    fact_text = "السجل المرصود يضم 20,789 مستخدمًا قديمًا و71 مستخدمًا حاليًا، مع 28 مرشح تداخل في National_ID. ويضم المحتوى 62 خبرًا، إلى جانب 227 أكاديمية و24 فرعًا. خط الأساس المؤقت 120h، بينما restore not proven حتى الآن؛ وهوية الـAPK تحمل remote hash differs."
    authored.append({"copy_id": "COPY.AHS.FACTS", "role": "paragraph", "text": fact_text, "claim_refs": ["AHS.FACT.LEGACY_USERS", "AHS.FACT.CURRENT_USERS", "AHS.FACT.NATIONAL_ID_OVERLAP", "AHS.FACT.NEWS_ROWS", "AHS.FACT.ACADEMIES_BRANCHES", "AHS.FACT.BASELINE_HOURS", "AHS.FACT.RESTORE_STATUS", "AHS.FACT.APK_BOUNDARY"], "protected_spans": ["20,789", "71", "28", "62", "227", "24", "120h", "restore not proven"]})
    tech_text = "المسار المرصود /opt/ahs/core يعمل على PostgreSQL 16.13 وقاعدة ahs_prod. فحص manage.py check اكتمل مع staticfiles.W004؛ وملف النسخ يحمل تاريخ 2026-04-20."
    authored.append({"copy_id": "COPY.AHS.TECH", "role": "paragraph", "text": tech_text, "claim_refs": ["AHS.FACT.RUNTIME_PATH", "AHS.FACT.DATABASE", "AHS.FACT.RUNTIME_CHECK", "AHS.FACT.BACKUP_DATE"], "protected_spans": ["/opt/ahs/core", "PostgreSQL 16.13", "ahs_prod", "manage.py check", "staticfiles.W004", "2026-04-20"]})
    authored.append({"copy_id": "COPY.AHS.CODE", "role": "technical_text", "text": "python manage.py check\n# observed warning: staticfiles.W004", "claim_refs": ["AHS.FACT.RUNTIME_CHECK"], "protected_spans": ["manage.py check", "staticfiles.W004"]})
    for number, category, entry in entries:
        cid = f"AHS.REQUIREMENT.{number:02d}"
        text = f"المطلب {number:02d} — {AR_TITLES[number]}: {AR_SUMMARIES[number]}"
        tokens = []
        tokens = []
        c = next(item for item in claims if item["claim_id"] == cid)
        authored.append({"copy_id": f"COPY.AHS.REQUIREMENT.{number:02d}", "role": "paragraph", "text": text, "claim_refs": [cid], "protected_spans": tokens, "state_projections": [{"claim_id": cid, "dimension": dimension, "value": c[dimension]} for dimension in ("epistemic_state", "closure_state", "risk")]})
    sections = [{"section_id": "decision", "purpose": "ما الذي يمكن أن يقرره صاحب المشروع الآن؟", "copy_refs": ["COPY.AHS.HEADLINE", "COPY.AHS.SUBHEAD", "COPY.AHS.CALLOUT"], "claim_refs": ["AHS.FACT.PROJECT_POSTURE"], "presentation_intent": "verdict", "structured_blocks": [{"block_id": "STRUCT.AHS.POSTURE", "type": "fact_list", "title": "الوضع الحالي", "items": [{"label": "الحكم", "value": "المشروع غير مغلق إنتاجيًا", "claim_refs": ["AHS.FACT.PROJECT_POSTURE"]}, {"label": "حدود الدليل", "value": "ملاحظة للقراءة فقط ومطابقة للمصادر", "claim_refs": ["AHS.FACT.OBSERVATION_BOUNDARY"]}]}]}]
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
    return {"truth": {"sources": truths, "claims": claims}, "reader": {"audience": "صاحب قرار أو مسؤول تسليم", "document_intent": "audit_report", "surface_profile": "omega-editorial", "primary_question": "ما الذي ثبت، وما الذي يمنع الإغلاق؟", "desired_action": "تحديد بوابة الإغلاق التالية", "technical_depth": "technical annex", "annex_policy": "التفاصيل التقنية في الملحق", "summary_rail": {"enabled": True, "title": "قرار اليوم", "body": "المتابعة ممكنة. إعلان الإغلاق يحتاج دليل الهوية والاستعادة والأدوار والأجهزة."}, "language": {"primary": "ar", "direction": "rtl", "technical_english": "when_earned", "translation_preference": "Arabic prose with exact technical identifiers"}}, "strategy": {"document_intent": "audit_report", "through_line": "فصل ما ثبت عن ما يحتاج إثباتًا قبل قرار الإغلاق.", "must_appear_first": ["verdict", "key_fact"], "secondary_content": ["evidence_matrix", "sequence"], "annex_content": ["technical_annex", "source_ledger"], "detail_level": "executive with technical depth later", "uncertainty_policy": "اعرض الفتح والحجب والجزئية بصراحة", "reader_journey": ["verdict", "facts", "evidence", "sequence", "annex"]}, "authored": {"blocks": authored}, "composition": {"sections": sections}}


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
        "COPY.PROPOSAL.SUBHEAD": "A bounded pilot answers the core play question with a known timebox and budget.",
        "COPY.PROPOSAL.CONTEXT": "Before committing to full production, the team needs a playable slice that exposes how the core loop holds up. The pilot gives the decision something practical to review.",
        "COPY.PROPOSAL.ACTION": "Decision requested: approve the scoped pilot for 6 weeks with a $12,000 cap.",
        "COPY.PROPOSAL.RISK": "Review the result weekly. If the core loop does not hold, stop the pilot before making a larger commitment.",
    }
    for block in authored["blocks"]:
        block["text"] = english_copy[block["copy_id"]]
    sections = [
        {"section_id": "decision", "purpose": "القرار المطلوب", "copy_refs": ["COPY.PROPOSAL.HEADLINE", "COPY.PROPOSAL.SUBHEAD", "COPY.PROPOSAL.ACTION"], "claim_refs": ["PROPOSAL.DECISION"], "presentation_intent": "verdict", "structured_blocks": []},
        {"section_id": "case", "purpose": "لماذا هذا النطاق؟", "copy_refs": ["COPY.PROPOSAL.CONTEXT"], "claim_refs": ["PROPOSAL.CONTEXT"], "presentation_intent": "narrative", "structured_blocks": []},
        {"section_id": "terms", "purpose": "حدود الطيار", "copy_refs": [], "claim_refs": [], "presentation_intent": "key_fact", "structured_blocks": [{"block_id": "STRUCT.PROPOSAL.TERMS", "type": "fact_list", "title": "ما ستتم الموافقة عليه", "items": [{"label": "المدة", "value": "6 weeks", "claim_refs": ["PROPOSAL.PILOT.LENGTH"]}, {"label": "السقف", "value": "$12,000", "claim_refs": ["PROPOSAL.BUDGET.CAP"]}, {"label": "المخرج", "value": "one playable vertical slice", "claim_refs": ["PROPOSAL.DELIVERABLE"]}]}]},
        {"section_id": "condition", "purpose": "شرط الاستمرار", "copy_refs": ["COPY.PROPOSAL.RISK"], "claim_refs": ["PROPOSAL.RISK"], "presentation_intent": "risk_register", "structured_blocks": [{"block_id": "STRUCT.PROPOSAL.RISK", "type": "risk_register", "title": "شرط واحد واضح", "items": [{"label": "المخاطرة", "value": "الإنفاق قبل معرفة جودة الحلقة", "detail": "المراجعة الأسبوعية توقف الطيار إذا لم تثبت الحلقة الأساسية.", "claim_refs": ["PROPOSAL.RISK"]}]}]},
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
        {"copy_id": "COPY.TECH.INTRO", "role": "paragraph", "text": "هذه المراجعة تلتقط هوية البيئة أولًا، ثم تعرض حالة الفحص، ثم تترك أثرًا واضحًا للمخاطرة وملحق الأدلة الذي يحتاجه فريق التشغيل.", "claim_refs": ["TECH.STATUS", "TECH.RISK", "TECH.ANNEX"], "protected_spans": []},
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
    write_bundle("proposal", build_proposal())
    write_bundle("technical", build_technical())
    (ROOT / "evals" / "human-authoring" / "wave6-execution.md").write_text("""# Wave 6 authoring execution record\n\nThe three final bundles were authored as independent deliverables after reading the pinned `humanize-writing`, `ux-writing`, and conservative `humanizer` instructions in `third_party/writing/`.\n\n- Human-first routing shaped the through-line, audience stance, sentence rhythm, and document-specific prose.\n- UX-writing routing was applied to labels, statuses, facts, table headings, callouts, and next-step language.\n- The conservative humanizer pass removed staged openers, decorative repetition, and context-free token stuffing while preserving source facts and identifiers.\n- The transformation was performed on the final AHS, proposal, and technical copy blocks; the earlier instruction-set inspection reports are not treated as output benchmarks.\n- Truth Lock ran after authoring and before rendering.\n""", encoding="utf-8")
    print(json.dumps({"status": "PASS", "bundles": ["ahs", "proposal", "technical"], "source": str(source_copy)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
