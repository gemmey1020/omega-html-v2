import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_omega_html_v2.py"
FIXTURE = ROOT / "evals" / "bundles" / "proposal"


class BuildWorkflowTest(unittest.TestCase):
    def run_build(self, *args):
        return subprocess.run([sys.executable, str(BUILD), *map(str, args)], text=True, capture_output=True)

    def test_markdown_build_emits_artifact_bundle_and_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "brief.md"
            source.write_text("# Release brief\n\nVERIFIED: Scope is approved.\n\n## Next\n\n- Confirm launch window.\n")
            completed = self.run_build("--input", source, "--source-type", "markdown", "--output-dir", root / "out", "--profile", "cyan", "--recipe", "executive-decision")
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "PASS")
            receipt = json.loads(Path(result["receipt"]).read_text())
            self.assertEqual(receipt["profile"], "omega-cyan")
            self.assertEqual(receipt["validation"]["semantic"], "PASS")
            self.assertEqual(receipt["validation"]["rendered"], "PASS")
            self.assertEqual(len(receipt["artifact_sha256"]), 64)
            self.assertTrue(Path(result["html"]).is_file())

    def test_bundle_build_does_not_reauthor_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = self.run_build("--bundle", FIXTURE, "--output-dir", Path(directory) / "out", "--profile", "silver")
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = json.loads(completed.stdout)
            receipt = json.loads(Path(result["receipt"]).read_text())
            self.assertEqual(receipt["input_mode"], "bundle")
            self.assertEqual(receipt["profile"], "omega-silver")
            self.assertTrue((Path(result["bundle"]) / "truth-model.json").is_file())

    def test_invalid_input_leaves_no_passing_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            completed = self.run_build("--text", " ", "--output-dir", output)
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse((output / "build-receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
