from __future__ import annotations

from skillforge.security.audit import AuditLogger
from skillforge.security.permissions import PermissionValidator


class TestPermissionValidator:
    def test_network_default_denied(self):
        from skillforge.models.skill import Permission
        from skillforge.security.permissions import PermissionError

        p = PermissionValidator(Permission())
        import pytest

        with pytest.raises(PermissionError):
            p.check_network()

    def test_network_allowed(self):
        from skillforge.models.skill import Permission

        p = PermissionValidator(Permission(network=True))
        assert p.check_network()

    def test_file_read_allowed(self):
        from skillforge.models.skill import Permission

        p = PermissionValidator(Permission(filesystem_read=["/tmp"]))
        assert p.check_file_read("/tmp/test.txt")

    def test_file_read_denied(self):
        from skillforge.models.skill import Permission
        from skillforge.security.permissions import PermissionError

        p = PermissionValidator(Permission(filesystem_read=["/tmp"]))
        import pytest

        with pytest.raises(PermissionError):
            p.check_file_read("/etc/passwd")

    def test_environ(self):
        from skillforge.models.skill import Permission

        p = PermissionValidator(Permission(env_vars=["MY_VAR"]))
        assert p.check_env_var("MY_VAR")

    def test_dangerous_denied(self):
        from skillforge.models.skill import Permission
        from skillforge.security.permissions import PermissionError

        p = PermissionValidator(Permission())
        import pytest

        with pytest.raises(PermissionError):
            p.check_dangerous()


class TestAuditLogger:
    def test_log_and_recover(self, tmp_path):
        log_path = tmp_path / "audit.log"
        audit = AuditLogger(log_path=log_path)

        audit.log_execution("test-skill", "completed", duration_ms=100)
        audit.log_install("test-skill", "1.0.0", "local")
        audit.log_remove("test-skill", "1.0.0")

        entries = audit.get_recent()
        assert len(entries) == 3
        assert entries[0]["event"] == "skill.execution"
        assert entries[1]["event"] == "skill.install"
        assert entries[2]["event"] == "skill.remove"

    def test_sanitization(self, tmp_path):
        log_path = tmp_path / "audit_sanitize.log"
        audit = AuditLogger(log_path=log_path)

        audit.log_execution(
            "test",
            "completed",
            inputs={"api_key": "secret-123", "name": "normal", "token": "abc"},
        )

        entries = audit.get_recent()
        assert len(entries) == 1
        assert entries[0]["details"]["inputs"]["api_key"] == "***"
        assert entries[0]["details"]["inputs"]["token"] == "***"
        assert entries[0]["details"]["inputs"]["name"] == "normal"
