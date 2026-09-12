---
name: omega-html-v2-candidate
description: Parallel candidate for general-purpose human-facing Omega HTML artifacts.
---

# Omega HTML v2 Candidate

This is a non-promoted candidate. It is intended for human-facing reports and
documents, not AHS-specific behavior.

## Scope foundation

- Truth and evidence come before presentation.
- Audience and purpose come before composition.
- Omega identity remains consistent and deliberate.
- Arabic-first and mixed RTL/LTR content must remain readable; technical
  identifiers stay safely isolated.
- This candidate does not own websites or application UI.
- This candidate does not own PDF export or PDF QA.

The semantic boundaries are defined by Truth, Reader Brief, Document Strategy,
Authored Content, and Composition contracts under `references/` and `schemas/`.
Gate 4 freezes a candidate human-authoring layer with Arabic-first policy,
role-based copy routing, optional evidence-backed voice adaptation, and a
conservative final prose pass. Truth Lock remains authoritative before and
after authoring.
Wave 5 adds semantic information architecture, tokenized surface profiles,
standalone HTML rendering, artifact checks, responsive/print CSS, and local
browser screenshot QA. It remains a non-promoted candidate.
The final authoring and rendering pipeline is not implemented yet. The installed `/home/jemy/.codex/skills/omega-html/` remains the live
v1 skill and is not modified by this candidate.
