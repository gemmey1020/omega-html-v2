from pathlib import Path
import hashlib


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "skills" / "omega-html-v2-candidate"
V1 = Path("/home/jemy/.codex/skills/omega-html")
MANIFEST = CANDIDATE / "manifests" / "v1-manifest.tsv"


def test_v1_manifest_exists():
    assert MANIFEST.is_file()
    assert "SKILL.md\t" in MANIFEST.read_text()


def test_candidate_does_not_point_output_at_installed_v1():
    assert not str(CANDIDATE).startswith(str(V1))
    assert not (CANDIDATE / "output").exists()


def test_live_v1_matches_frozen_manifest():
    for line in MANIFEST.read_text().splitlines()[1:]:
        if not line or line.startswith("#"):
            continue
        relative, expected, _size = line.split("\t")
        actual = hashlib.sha256((V1 / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
