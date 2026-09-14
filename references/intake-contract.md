# Intake contract

Omega HTML v2 accepts either an inline prompt or a UTF-8 Markdown file. The compiler preserves supplied wording and converts it into the five semantic contracts; it does not research, infer missing facts, or upgrade confidence.

## Evidence labels

Paragraphs or list items may begin with `VERIFIED:`, `USER-STATED:`, `UNKNOWN:`, `INFERRED:`, `NOT-FOUND:`, or `CONFLICT:`. Unlabelled content is conservatively `source_backed`, `open`, and `medium` risk. The first content claim is material so Truth Lock requires it to remain authored and composed.

## Markdown subset

- One `#` title.
- `##` section headings.
- Paragraphs.
- `-` or `*` lists, emitted as checklists.
- Pipe tables with a separator row, emitted as tables.

Raw input remains JSON data. HTML escaping belongs to the renderer, so prompt text is never interpreted as executable markup.
