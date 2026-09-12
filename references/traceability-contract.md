# Traceability Contract

## Source → Claim
Truth owns a `sources` registry. Each claim's `source_refs` must resolve to a
registered `source_id`; the validator does not retrieve or verify sources.

## Claim → Authored Copy
Each copy block has a stable `copy_id` and `claim_refs`. Material claims must
be referenced by at least one authored block.

## Copy → Composition
Composition `copy_refs` must resolve to authored blocks. Direct section
`claim_refs` are also checked. A material claim must be reachable in either
way to count as composed.

## Protected Exact Values
Truth `protected_tokens` authorize exact `protected_spans` in copy text.
Spans must occur verbatim and may not be duplicated. This is declared-token
protection only.

## Material Coverage
Metrics count unique claims with `materiality: material`, then unique material
claims authored and uniquely reachable in Composition.

## Structured State Projection
Projections communicate `epistemic_state`, `closure_state`, or `risk`. Missing
claim/linkage is `INVALID_STATE_PROJECTION`; a valid projection with a wrong
value is `STATE_PROJECTION_MISMATCH`.

## Error Model
Valid bundles return structured JSON with exit `0`. Normal schema or semantic
validation failures return JSON with stable error codes and exit `2`; coverage
is emitted only when it can be computed safely.

## Coverage Metrics
`material_claims`, `authored_material_claims`, and `composed_material_claims`
are unique-ID counts, not occurrence counts.

## Guarantees
The runtime proves schema validity, structural IDs and references, declared
exact-token carriage, structured projections, and material reachability.

## Non-Guarantees
It does not prove source truthfulness, freshness, retrieval, arbitrary prose
semantic equivalence, or detect every unmarked factual invention.
