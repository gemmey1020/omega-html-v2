# Omega HTML v2 Candidate

Omega HTML v2 is an experimental Codex skill for producing standalone, evidence-aware HTML reports, briefs, audits, proposals, and technical documents in Arabic and English.

It treats the semantic bundle as the source of truth, keeps document intent separate from visual profile, and validates the generated artifact for structure, language and direction, claim traceability, profile consistency, and remote dependencies.

## Status

This is a candidate, not a promoted or production release. The foundation and semantic contracts are present; further authoring, visual, and technical gates remain before promotion. It does not replace the installed Omega HTML v1 skill.

## Contents

- `scripts/` — intake compilation, bundle validation, rendering, artifact validation, and build workflow
- `schemas/` — semantic bundle contracts
- `config/` — authoring routes, document recipes, and surface profiles
- `references/` — authoring, truth, composition, language, and output contracts
- `evals/` and `tests/` — examples and evaluation material
- `third_party/writing/` — selected upstream writing skills; each retains its upstream license and source notice

## Use

The entry point for the Codex skill is `SKILL.md`. It describes input routing, bundle contracts, profiles, rendering, validation, and the completion criteria. The Python tools are under `scripts/`.

## License

No license has been selected for the original project code. The files under `third_party/writing/` remain under their respective upstream licenses; see their `LICENSE` and `UPSTREAM.md` files.
