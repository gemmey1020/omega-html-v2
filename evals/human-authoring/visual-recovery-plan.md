# Omega HTML v2 Visual Recovery Plan

## Evidence baseline

The current candidate was opened through Playwright at desktop (`1440 x 1100`) and mobile (`390 x 844`) viewports, then screenshots were inspected locally. The current AHS wastes the desktop canvas with a narrow right-hand content column, repeats the same table grammar across every section, and makes the evidence ledger read like a compressed data dump. The proposal has an oversized headline, a weak decision surface, and Arabic copy inside an English document. The technical artifact has the same narrow-column problem and reads as an internal dark HUD rather than a polished technical brief.

The legacy AHS gold artifact was inspected as a visual reference for stronger Omega identity, but it is treated as a palette and hierarchy reference only; its card-heavy structure is not copied.

## Routed design handoff

```yaml
ui_product_handoff:
  lane: refinement
  mode: product-intervention
  source_status: browser-evidence
  protected_constraints:
    - truth-model claims, source references, and closure states
    - Truth Lock and rendered-artifact validation contracts
    - material claim and copy traceability
    - Arabic-first AHS language and precise technical identifiers
    - standalone HTML with no remote dependencies
  primary_worker: premium_ui_generator
  secondary_worker: null
  handoff_reason: rescue the rendered documents from narrow-column, repetitive, and system-generated presentation
  blocked_by: []
  proof_needed:
    - Playwright desktop and mobile captures for all three artifacts
    - visual inspection of accepted screenshots
    - print export and rendered-page inspection
    - Truth Lock and artifact-validator PASS
```

## Visual thesis

Omega v2 should read as a calm, editorial decision instrument: warm paper and precise ink for executive review, restrained mineral color for proposals, and a dark ink-and-teal technical sheet only where technical density benefits from it. Typography, alignment, and whitespace carry the hierarchy. Rules and tables are used as evidence infrastructure, not decoration.

## Implementation direction

1. Rebuild the AHS first with a full-width editorial grid, a compact decision header, a measurable truth strip, and wide evidence tables with deliberate row rhythm.
2. Remove the generic rail from the default reading surface; retain summary content only when it earns a clearly placed decision note.
3. Give each document intent a composition-specific layout while preserving all semantic references.
4. Use a small token system for page width, type scale, spacing, rules, accents, and print colors.
5. Make mobile a real reflow: readable Arabic measures, stacked evidence rows, no desktop-width tables, and no competing side column.
6. Use the improved AHS system as the golden reference, then adapt—not blindly clone—it for the proposal and technical artifact.

## Skill application

- `omega_ui_product_brain`: refinement lane and protected handoff.
- `frontend-skill`: poster/editorial visual thesis and first-viewport direction.
- `premium_ui_generator`: implementation/refinement direction.
- `design_system_enforcer`: token, spacing, typography, component, and responsive consistency.
- `product_flow_architect`: decision clarity for AHS, approval clarity for Proposal, and diagnostic clarity for Technical.
- `ui_taste_critic`: evidence-based hierarchy, density, typography, and polish review.
- `product-design/audit`: screenshot-first baseline audit.
- `playwright`: browser-rendered desktop/mobile captures and console inspection.
- `pdf`: browser print export, PDF metadata, font, and rendered-page QA.

Figma and image-to-code routes are not used because this task has no authoritative Figma frame or selected visual mock; the current rendered artifacts and local Omega references are the available visual evidence.
