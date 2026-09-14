import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "compile_intake.py"
VALIDATOR = ROOT / "scripts" / "validate_semantic_bundle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("compile_intake", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("intake compiler unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IntakeCompilerTest(unittest.TestCase):
    def test_markdown_compiles_to_valid_traceable_bundle(self):
        compiler = load_module()
        source = """# Release Decision

VERIFIED: The existing store accounts are active.

## Cost impact

- Firebase Cloud Messaging has no message transport fee.
- SMS recovery is usage-based.

| Service | Cost |
| --- | --- |
| FCM | No-cost |
"""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            result = compiler.compile_text(
                source,
                output,
                source_type="markdown",
                audience="executive leadership",
                language="en",
                recipe="executive-decision",
                profile="cyan",
                title=None,
                source_locator="release.md",
            )
            self.assertEqual(result["profile"], "omega-cyan")
            self.assertEqual(result["recipe"], "executive-decision")
            truth = json.loads((output / "truth-model.json").read_text())
            authored = json.loads((output / "authored-content.json").read_text())
            composition = json.loads((output / "composition-model.json").read_text())
            self.assertEqual(truth["claims"][0]["epistemic_state"], "observed")
            self.assertEqual(truth["claims"][0]["closure_state"], "verified")
            self.assertIn("Firebase Cloud Messaging", json.dumps(authored))
            types = [b["type"] for s in composition["sections"] for b in s.get("structured_blocks", [])]
            self.assertIn("checklist", types)
            self.assertIn("table", types)
            command = [sys.executable, str(VALIDATOR)]
            for flag, name in (("truth", "truth-model.json"), ("reader", "reader-brief.json"), ("strategy", "document-strategy.json"), ("authored", "authored-content.json"), ("composition", "composition-model.json")):
                command.extend([f"--{flag}", str(output / name)])
            completed = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_inline_prompt_is_escaped_and_uses_stable_ids(self):
        compiler = load_module()
        source = "Decision <script>alert(1)</script> is pending.\n\nUNKNOWN: Provider approval time."
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            kwargs = dict(source_type="prompt", audience="operations", language="en", recipe="proposal", profile="gold", title="Release <Brief>", source_locator="inline prompt")
            compiler.compile_text(source, Path(first), **kwargs)
            compiler.compile_text(source, Path(second), **kwargs)
            first_truth = (Path(first) / "truth-model.json").read_text()
            second_truth = (Path(second) / "truth-model.json").read_text()
            self.assertEqual(first_truth, second_truth)
            self.assertIn("<script>", first_truth)
            normalized = json.loads((Path(first) / "normalized-request.json").read_text())
            self.assertEqual(normalized["title"], "Release <Brief>")
            self.assertEqual(normalized["direction"], "ltr")

    def test_empty_input_is_rejected(self):
        compiler = load_module()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Input text is empty"):
                compiler.compile_text("  ", Path(directory), source_type="prompt", audience="executive", language="en", recipe=None, profile="cyan", title=None, source_locator="inline")


if __name__ == "__main__":
    unittest.main()
