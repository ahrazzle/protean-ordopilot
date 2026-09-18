"""5. handoff-compression: long session -> HandoffRecord <= 2000 chars,
pointer-only, truncated flag correct."""
from courier import HANDOFF_BUDGET_CHARS, compactor


class TestHandoffCompression:
    def _items(self, n=30):
        return [{"summary": "decision %02d: " % i + "x" * 180,
                 "ref": "evt-%04d" % i} for i in range(n)]

    def test_bounded_and_truncated(self):
        rec = compactor.build_handoff("sess-a", self._items(),
                                      to_session_id="sess-b")
        assert rec["char_count"] <= HANDOFF_BUDGET_CHARS
        assert len(rec["summary"]) == rec["char_count"]
        assert rec["truncated"] is True
        # Newest-first input: items[0] is newest, kept at the front.
        assert rec["pointers"][0] == "evt-0000"
        assert rec["from_session_id"] == "sess-a"
        assert rec["to_session_id"] == "sess-b"

    def test_small_handoff_not_truncated(self):
        items = self._items(3)
        rec = compactor.build_handoff("sess-a", items)
        assert rec["truncated"] is False
        assert rec["pointers"] == ["evt-0000", "evt-0001", "evt-0002"]
        assert rec["char_count"] <= HANDOFF_BUDGET_CHARS

    def test_no_secrets_or_transcripts(self):
        items = [{"summary": "token sk-abcdefghijklmnop123456 burned",
                  "ref": "evt-1"}]
        rec = compactor.build_handoff("sess-a", items)
        assert "sk-abcdefghijklmnop123456" not in rec["summary"]
        assert "[REDACTED" in rec["summary"]
