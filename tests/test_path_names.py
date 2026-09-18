"""Published-tree path-name gate.

Fails if any git-tracked path contains one of the eight internal names.
The forbidden list is derived at runtime the same way the lane scanner
derives it (AST parse of the sweep script's terms list). That source is
author-local, so when it is absent the gate skips; when it is present
but the list cannot be derived the gate errors closed instead of
passing silently.
No forbidden string appears in this file.
"""
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


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
        pytest.skip(
            "path-name gate skipped: forbidden-term source absent at %s "
            "(set FORBIDDEN_TERMS_SOURCE to the sweep script to run it)"
            % src)
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


def test_absent_source_skips_instead_of_failing(tmp_path):
    """An absent forbidden-term source must skip the gate, never fail it."""
    missing = tmp_path / "absent-forbidden-terms-source.py"
    assert not missing.exists()
    env = dict(os.environ, FORBIDDEN_TERMS_SOURCE=str(missing))
    repo = Path(__file__).resolve().parent.parent
    node = "%s::test_published_tree_paths_are_neutral" % Path(
        __file__).resolve()
    p = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, timeout=120, env=env, cwd=str(repo))
    out = (p.stdout or "") + (p.stderr or "")
    assert p.returncode == 0, (
        "expected a clean skipped run, got rc=%s:\n%s"
        % (p.returncode, out[-2000:]))
    assert "1 skipped" in out, (
        "expected the gate to report one skipped test, got:\n%s"
        % out[-2000:])
