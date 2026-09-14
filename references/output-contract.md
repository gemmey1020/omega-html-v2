# Output contract

`scripts/build_omega_html_v2.py` is the reusable intake-to-artifact command. It accepts exactly one of `--text`, `--input`, or `--bundle` and writes atomically into an absent or empty output directory.

A profile is required for every build. Interactive callers must ask when the
user has not selected Cyan, Gold, or Silver; the command does not make a silent
profile choice.

Successful output contains:

- `omega-report.html`: standalone local-only HTML with Omega favicon and 1200 ms preloader.
- `semantic-bundle/`: the five validated semantic contracts plus `normalized-request.json`.
- `build-receipt.json`: canonical profile and recipe, semantic/rendered validation results, and SHA-256 hashes.

The build fails closed: it does not emit a passing receipt when intake, Truth Lock, rendering, or rendered-artifact validation fails. Screenshots and PDF export are optional downstream QA and are not silently claimed by this receipt.
