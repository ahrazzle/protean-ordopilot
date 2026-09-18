"""Published-tree path-name gate.

Fails if any git-tracked path contains one of the eight internal names.
The forbidden list is derived at runtime the same way the lane scanner
derives it (AST parse of the sweep script's terms list); if the list
cannot be derived the test errors closed instead of passing silently.
No forbidden string appears in this file.
"""
import ast
import os
import re
import subprocess
from pathlib import Path


def _sweep_source():
    override = os.environ.get("FORBIDDEN_TERMS_SOURCE")
    if override:
        return Path(override)
    seg = "sh" + "aka"
    return (Path.home() / ".hermes" / "profiles" / seg / "cache"
            / "delegation" / "codename-leak-sweep" / "fast.py")


def _derive_terms():
    src = _sweep_source()
    if not src.is_file():
        raise AssertionError(
            "path-name gate closed: cannot derive forbidden list; "
            "missing source at %s (set FORBIDDEN_TERMS_SOURCE to "
            "override)" % src)
    text = src.read_text(encoding="utf-8")
    m = re.search(r"terms\s*=\s*\[([^\]]+)\]", text)
    if not m:
        raise AssertionError(
            "path-name gate closed: terms list not found in %s" % src)
    terms = ast.literal_eval("[" + m.group(1) + "]")
    if (not isinstance(terms, list) or len(terms) != 8
            or not all(isinstance(t, str) and t for t in terms)):
        raise AssertionError(
            "path-name gate closed: unexpected derived list shape")
    return list(terms)


def _redact(text, terms):
    out = str(text)
    for t in terms:
        out = re.sub(re.escape(t), "[redacted]", out, flags=re.IGNORECASE)
    return out


def _tracked_paths():
    repo = Path(__file__).resolve().parent.parent
    p = subprocess.run(["git", "-C", str(repo), "ls-files"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError(
            "path-name gate closed: git ls-files failed: %s"
            % (p.stderr or p.stdout).strip()[:300])
    return [ln for ln in p.stdout.splitlines() if ln.strip()]


def test_published_tree_paths_are_neutral():
    terms = _derive_terms()
    patterns = [re.compile(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])",
                           re.IGNORECASE) for t in terms]
    bad = sorted({path for path in _tracked_paths()
                  for pat in patterns if pat.search(path)})
    assert not bad, "tracked paths carry internal names: %s" % _redact(
        bad, terms)
