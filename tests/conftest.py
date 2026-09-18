import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from courier.adapters.local import LocalBackend  # noqa: E402
from courier.catalog import SessionCatalog  # noqa: E402
from courier.ledger import DeliveryLedger  # noqa: E402


@pytest.fixture
def state(tmp_path):
    home = str(tmp_path / "courier-state")
    os.makedirs(home, exist_ok=True)
    catalog = SessionCatalog(os.path.join(home, "routing_projection.json"))
    ledger = DeliveryLedger(os.path.join(home, "ledger.sqlite"))
    backend = LocalBackend()
    yield {"home": home, "catalog": catalog, "ledger": ledger,
           "backend": backend}
    ledger.close()


def seed(catalog, backend, items):
    refs = []
    for slug, summary in items:
        ref = catalog.create_session(slug, summary=summary)
        backend.seed(slug, summary, session_id=ref["session_id"])
        refs.append(ref)
    return refs


def redacted_msg(text, **kw):
    from courier import intake, redact
    return redact.redact_message(intake.make_message(text, **kw))[0]


def sessions_of(catalog):
    return [{"session_id": s["session_id"], "slug": s["slug"],
             "summary": s.get("summary", "")}
            for s in catalog.list_sessions()]
