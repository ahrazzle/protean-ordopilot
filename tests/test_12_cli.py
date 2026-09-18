"""12. cli-path: every verb end-to-end against the local backend with
exit-code assertions."""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCliPath:
    def run(self, home, *argv):
        env = dict(os.environ, ORDA_STATE_HOME=home,
                   PYTHONPATH=REPO + os.pathsep +
                   os.environ.get("PYTHONPATH", ""))
        return subprocess.run(
            [sys.executable, "-m", "orda", "--state-home", home, *argv],
            cwd=REPO, capture_output=True, text=True, env=env, timeout=60)

    def out(self, proc):
        assert proc.stdout.strip(), proc.stderr
        return json.loads(proc.stdout)

    def test_all_verbs(self, tmp_path):
        from orda.catalog import SessionCatalog
        home = str(tmp_path / "cli-state")
        os.makedirs(home, exist_ok=True)
        cat = SessionCatalog(os.path.join(home, "routing_projection.json"))
        cat.create_session("refund-policy",
                           summary="refund policy returns warranty claims")
        cat.create_session("billing",
                           summary="billing invoices payments charges")

        p = self.run(home, "topics")
        assert p.returncode == 0, p.stderr
        assert {"refund-policy", "billing"} <= {
            t["slug"] for t in self.out(p)["topics"]}

        p = self.run(home, "show", "refund-policy")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["session"]["revision"] == 1

        p = self.run(home, "route", "What is our refund policy here?")
        assert p.returncode == 0, p.stderr
        routed = self.out(p)
        assert routed["dispatch"]["result"] == "delivered"
        mid = routed["dispatch"]["message_id"]

        # Same text -> duplicate-ack, still exit 0.
        p = self.run(home, "route", "What is our refund policy here?")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["dispatch"]["result"] == "duplicate-ack"

        p = self.run(home, "inspect", mid)
        assert p.returncode == 0, p.stderr
        assert self.out(p)["record"]["message_id"] == mid

        p = self.run(home, "correct", mid, "--to", "billing")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["rerouted_to"]

        p = self.run(home, "merge", "refund-policy", "billing",
                     "--into", "support")
        assert p.returncode == 0, p.stderr

        p = self.run(home, "split", "support", "--at", mid, "--new", "vip")
        assert p.returncode == 0, p.stderr

        p = self.run(home, "pause", "vip")
        assert p.returncode == 0, p.stderr
        p = self.run(home, "route", "/vip urgent question")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["dispatch"]["result"] == "parked-clarification"
        p = self.run(home, "resume", "vip")
        assert p.returncode == 0, p.stderr

        p = self.run(home, "route", "please delete the archive folder")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["dispatch"]["result"] == "held-for-approval"

        p = self.run(home, "approvals")
        assert p.returncode == 0, p.stderr
        pending = self.out(p)["pending"]
        assert len(pending) == 1
        p = self.run(home, "approvals", "--approve", pending[0]["id"])
        assert p.returncode == 0, p.stderr
        p = self.run(home, "approvals", "--deny", "apr-nope")
        assert p.returncode == 5

        p = self.run(home, "forget", "vip")
        assert p.returncode == 0, p.stderr
        p = self.run(home, "show", "vip")
        assert p.returncode == 5
        p = self.run(home, "forget", "support", "--drop-ledger")
        assert p.returncode == 2  # --confirm required

        p = self.run(home, "doctor")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["ok"] is True

        p = self.run(home, "status")
        assert p.returncode == 0, p.stderr
        assert self.out(p)["sessions"] >= 1

        # Error paths.
        assert self.run(home, "show", "nope").returncode == 5
        assert self.run(home, "inspect", "nope").returncode == 5
        assert self.run(home, "correct", "nope",
                        "--to", "support").returncode == 5
        assert self.run(home, "merge", "a", "b",
                        "--into", "c").returncode == 5
