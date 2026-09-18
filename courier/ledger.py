"""Delivery ledger: SQLite + JSONL mirror with idempotency keys.

idempotency_key = sha256(canonical_hash + "|" + target_session_id).
Duplicate key -> drop-and-ack (return the ORIGINAL record, never redeliver).
The payload column holds only the canonical hash, never message text.
"""

import hashlib
import json
import os
import sqlite3

from .intake import utcnow_rfc3339

SCHEMA = """CREATE TABLE IF NOT EXISTS deliveries (
  idempotency_key TEXT PRIMARY KEY,
  record TEXT NOT NULL,
  ts TEXT NOT NULL
)"""


def idempotency_key(canonical_hash, target_session_id):
    return hashlib.sha256(
        ("%s|%s" % (canonical_hash, target_session_id)).encode("utf-8")
    ).hexdigest()


class DeliveryLedger:
    def __init__(self, sqlite_path, jsonl_path=None):
        self.sqlite_path = sqlite_path
        self.jsonl_path = jsonl_path or (os.path.splitext(sqlite_path)[0] +
                                         ".jsonl")
        os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)),
                    exist_ok=True)
        self._conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def _sanitize(self, record):
        rec = {k: v for k, v in dict(record).items()
               if k not in ("text", "payload", "body")}
        return rec

    def record(self, delivery):
        """Insert; on UNIQUE conflict return ('duplicate', original)."""
        rec = self._sanitize(delivery)
        rec.setdefault("ts_utc", utcnow_rfc3339())
        key = rec.get("idempotency_key")
        if not key:
            raise ValueError("delivery needs idempotency_key")
        try:
            self._conn.execute(
                "INSERT INTO deliveries(idempotency_key, record, ts) "
                "VALUES (?,?,?)",
                (key, json.dumps(rec, sort_keys=True), rec["ts_utc"]))
            self._conn.commit()
        except sqlite3.IntegrityError:
            return "duplicate", self.get(key)
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        return "inserted", rec

    def get(self, key):
        cur = self._conn.execute(
            "SELECT record FROM deliveries WHERE idempotency_key=?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def find_by_message(self, message_id):
        cur = self._conn.execute("SELECT record FROM deliveries")
        for (blob,) in cur.fetchall():
            rec = json.loads(blob)
            if rec.get("message_id") == message_id:
                return rec
        return None

    def recent_for_session(self, session_id, limit=20):
        cur = self._conn.execute(
            "SELECT record FROM deliveries ORDER BY ts DESC LIMIT ?",
            (limit * 5,))
        out = []
        for (blob,) in cur.fetchall():
            rec = json.loads(blob)
            if rec.get("target_session_id") == session_id:
                out.append(rec)
                if len(out) >= limit:
                    break
        return out

    def count(self):
        cur = self._conn.execute("SELECT COUNT(*) FROM deliveries")
        return cur.fetchone()[0]

    def anonymize_session(self, session_id):
        """Forget-verb helper: strip message links for a session's rows."""
        cur = self._conn.execute("SELECT idempotency_key, record "
                                 "FROM deliveries")
        n = 0
        for key, blob in cur.fetchall():
            rec = json.loads(blob)
            if rec.get("target_session_id") == session_id:
                rec["message_id"] = "forgotten"
                rec["canonical_hash"] = "forgotten"
                rec["anonymized"] = True
                self._conn.execute(
                    "UPDATE deliveries SET record=? WHERE idempotency_key=?",
                    (json.dumps(rec, sort_keys=True), key))
                n += 1
        self._conn.commit()
        return n

    def drop_session(self, session_id):
        cur = self._conn.execute("SELECT idempotency_key, record "
                                 "FROM deliveries")
        keys = [k for k, blob in cur.fetchall()
                if json.loads(blob).get("target_session_id") == session_id]
        for k in keys:
            self._conn.execute(
                "DELETE FROM deliveries WHERE idempotency_key=?", (k,))
        self._conn.commit()
        return len(keys)

    def close(self):
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass
