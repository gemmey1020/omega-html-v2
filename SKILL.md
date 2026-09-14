---
name: omega-html-v2
description: Turn a prompt, Markdown source, or evidence-backed semantic bundle into a validated standalone Omega HTML report or HUD brief with human-facing Arabic or English prose, purposeful composition, traceability, and responsive RTL/LTR profiles.
---

# Omega HTML v2

Use for a human-facing Omega report, proposal, audit, executive decision,
commercial framework, or dense technical document. It is not the installed
production skill until explicitly promoted.

## Input routing

- Use `scripts/build_omega_html_v2.py` for prompt, Markdown, or bundle input.
- Prompt and Markdown are compiled conservatively into the five-file semantic bundle.
- Use a prepared bundle when claim-level evidence and composition need explicit control.
- Resolve the document recipe independently from its visual profile.
- Read `references/intake-contract.md` for prompt or Markdown compilation.
- Read `references/output-contract.md` for generated artifacts and receipts.

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

## Recipes and visual composition

Choose a recipe from `config/recipes.json` to shape the reader journey. Choose
a surface profile independently from document intent through
`config/profiles.json`. Keep type scale,
line length, rhythm, contrast, and whitespace proportional to the document's
job. Use quiet editorial support for decision documents and restrained HUD
tokens for technical surfaces. The optional `omega-gold`, `omega-teal`, and
`omega-cyan` profiles preserve the same traceability contract. Use Gold for
executive luxury, Cyan for operational decisions, Teal for calm operations,
Silver for internal evidence. These three are the primary production profiles,
with Cyan as the default. Aion and Hints remain experimental and must be chosen
explicitly; the remaining profiles are supported compatibility surfaces.
Profiles must change geometry, density, and hero
treatment as well as palette. Do not leak machine enums into reader copy,
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
modify an installed predecessor, install itself globally, or invent unsupported
facts, metrics, evidence, or conclusions.

## Output and definition of done

Return the absolute artifact paths, selected recipe/profile, and validation
receipt. Done means the
bundle passes Truth Lock, the artifact passes structural validation, copy is
traceable, Arabic/English direction is readable, the document is standalone,
responsive and print-aware, and the final desktop/mobile screenshots have been
reviewed when visual QA is in scope. Keep the candidate isolated until an
explicit promotion decision.
