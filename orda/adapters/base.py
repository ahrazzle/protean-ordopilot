"""SessionBackend protocol: the only seam between core and session stores.

Core codes to this protocol; Hermes/local/fake backends implement it.
"""

from typing import Protocol


class SessionBackend(Protocol):
    def list_sessions(self):
        """Return [{session_id, slug, summary}]."""
        ...  # pragma: no cover

    def get_session(self, session_id):
        """Return session dict or None."""
        ...  # pragma: no cover

    def create_session(self, slug, summary=""):
        """Create and return session dict."""
        ...  # pragma: no cover

    def append_message(self, session_id, message):
        """Deliver a (redacted) message; return receipt dict."""
        ...  # pragma: no cover

    def resume_session(self, session_id, prompt):
        """Resume a session with a prompt; return result dict."""
        ...  # pragma: no cover
