"""Tests for scripts/measure_guide.py — the guide measurement method."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from measure_guide import count, strip_markers  # noqa: E402


def test_words_are_regex_tokens():
    words, sentences = count("Hello there. Two words!\n")
    assert words == 4
    assert sentences == 2


def test_headings_list_and_quote_markers_do_not_add_words():
    plain, _ = count("Orda guide text here.")
    marked, _ = count("# Orda guide text here.\n- Orda guide text here.\n> Orda guide text here.")
    assert marked == plain * 3  # markers stripped; only real words counted


def test_table_pipes_and_separator_rows_are_ignored():
    text = "| A result | Another result |\n|---|---|\n| One two | Three four five. |"
    words, sentences = count(text)
    assert words == 9  # 4 + 5 real words; pipes and separator row add nothing
    assert sentences == 1  # separator row removed; one sentence span with words


def test_code_fences_are_excluded():
    text = "One two three.\n```\npipeline fail_next stage\n```\nFour five."
    words, sentences = count(text)
    assert words == 5
    assert sentences == 2


def test_sentence_needs_a_word():
    words, sentences = count("Wait... ...then go!")
    assert words == 3
    assert sentences == 2


def test_strip_markers_removes_hashes_and_ticks():
    stripped = strip_markers("# Title\nUse `append_message` here.")
    assert "#" not in stripped
    assert "`" not in stripped


def test_nested_blockquote_and_heading_order():
    # Multiple blockquote markers and blockquote+heading/list ordering
    # must not leave marker characters that affect counts.
    assert strip_markers("> # Title") == "Title"
    assert strip_markers("> > nested quote") == "nested quote"
    assert strip_markers("> - Hello world.") == "Hello world."
    # Word count through the combined markers must equal the plain count
    assert count("> # Orda guide text here.")[0] == count("Orda guide text here.")[0]
    assert count("> - Orda guide text here.")[0] == count("Orda guide text here.")[0]
