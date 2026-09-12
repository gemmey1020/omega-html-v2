---
name: omega-html-v2-candidate
description: Generate standalone, printable Omega HTML documents from evidence-backed semantic bundles, with human-facing Arabic or English prose, purposeful information architecture, traceable structured content, and responsive RTL/LTR surfaces.
---

# Omega HTML v2 Candidate

Use for a human-facing Omega report, proposal, audit, or dense technical
document. The candidate emits one self-contained HTML artifact per input
bundle. It is not the installed production skill until explicitly promoted.

## Contract

- Truth Model is the source of facts, states, risks, evidence, and exact technical identifiers.
- Reader Brief names the audience, question, language, direction, and surface profile.
- Document Strategy sets the reader journey and places the decision before detail.
- Authored Content contains human-facing prose and explicit claim references.
- Composition contains semantic sections and general-purpose structured blocks; it never contains CSS or raw HTML.

## Authoring

Read the Reader Brief before writing. Route primary prose through the pinned
human-first instructions, compact labels/statuses/table headings through UX
writing, and conservative prose cleanup through the selected humanizer. Keep
Arabic syntax natural, use English only for earned technical names and exact
identifiers, and preserve uncertainty and protected facts. Run Truth Lock after
authoring and before rendering.

## Information architecture

Use semantic intents such as verdict, narrative, key fact, comparison, evidence
matrix, risk register, sequence, checklist, table, callout, technical block,
technical annex, and source ledger. Choose the smallest structure that helps
the reader: facts use definition lists, comparisons and matrices use tables,
sequences use ordered lists, checklists use lists, and code uses LTR preformatted
blocks. A rail is optional and must be justified by the Reader Brief.

## Visual composition

Choose a surface profile independently from document intent. Keep type scale,
line length, rhythm, contrast, and whitespace proportional to the document's
job. Use quiet editorial support for decision documents and restrained HUD
tokens for technical surfaces. Do not leak machine enums into reader copy,
repeat a generic dashboard layout, or force protected values into headlines.

## Rendering and validation

`scripts/render_artifact.py` validates the semantic bundle, emits local CSS with
no runtime dependency, records language/direction/theme metadata, and adds
`data-section-id`, `data-copy-id`, and `data-claim-id` traceability attributes.
It includes responsive and print rules and isolates technical LTR content.
`scripts/validate_rendered_artifact.py` parses the standalone artifact and
checks structure, metadata, profile purity, language/direction, no remote
dependencies or placeholders, composed copy reachability, material claim
traceability, and protected-token visibility.

## Non-goals

This skill does not build websites or application UIs, export or own PDFs,
modify the live `/home/jemy/.codex/skills/omega-html/` skill, install external
skills globally, or invent unsupported facts, metrics, evidence, or conclusions.

## Output and definition of done

Return the absolute HTML path and the selected surface profile. Done means the
bundle passes Truth Lock, the artifact passes structural validation, copy is
traceable, Arabic/English direction is readable, the document is standalone,
responsive and print-aware, and the final desktop/mobile screenshots have been
reviewed when visual QA is in scope. Keep the candidate isolated until an
explicit promotion decision.
