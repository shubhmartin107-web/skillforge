from __future__ import annotations

from pathlib import Path

from skillforge.security.permissions import (
    IntegrityError,
    PermissionError,
    PermissionValidator,
    generate_checksums_file,
    verify_against_checksums,
    verify_skill_integrity,
)
from skillforge.models.skill import Permission


class TestPermissionValidatorExtended:
    def test_validate_all_network(self):
        p = PermissionValidator(Permission(network=True))
        p.validate_all({"network": True})

    def test_validate_all_file_read(self):
        p = PermissionValidator(Permission(filesystem_read=["/tmp"]))
        p.validate_all({"file_read": "/tmp/test.txt"})

    def test_validate_all_fails(self):
        p = PermissionValidator(Permission())
        import pytest
        with pytest.raises(PermissionError):
            p.validate_all({"network": True})

    def test_file_read_star_allowed(self):
        p = PermissionValidator(Permission(filesystem_read=["*"]))
        assert p.check_file_read("/any/path/file.txt")

    def test_file_write_star_allowed(self):
        p = PermissionValidator(Permission(filesystem_write=["*"]))
        assert p.check_file_write("/any/path/file.txt")

    def test_file_write_denied(self):
        p = PermissionValidator(Permission(filesystem_write=[]))
        import pytest
        with pytest.raises(PermissionError):
            p.check_file_write("/tmp/test.txt")


class TestSkillIntegrity:
    def test_verify_integrity(self, tmp_path):
        (tmp_path / "skill.yaml").write_text("name: test\nversion: 1.0.0\n")
        (tmp_path / "skill.py").write_text("def run(): return {}\n")

        hashes = verify_skill_integrity(tmp_path)
        assert "skill.yaml" in hashes
        assert "skill.py" in hashes
        assert len(hashes) == 2

    def test_verify_against_checksums(self, tmp_path):
        (tmp_path / "skill.yaml").write_text("name: test\nversion: 1.0.0\n")
        (tmp_path / "skill.py").write_text("def run(): return {}\n")

        hashes = verify_skill_integrity(tmp_path)
        assert verify_against_checksums(tmp_path, hashes) is True

    def test_verify_fails_on_mismatch(self, tmp_path):
        (tmp_path / "skill.yaml").write_text("name: test\nversion: 1.0.0\n")

        hashes = verify_skill_integrity(tmp_path)
        hashes["skill.yaml"] = "badhash"
        (tmp_path / "skill.py").write_text("def run(): return {}\n")

        import pytest
        with pytest.raises(IntegrityError):
            verify_against_checksums(tmp_path, hashes)

    def test_generate_checksums_file(self, tmp_path):
        (tmp_path / "skill.yaml").write_text("name: test\n")
        result = generate_checksums_file(tmp_path)
        assert "skill.yaml" in result
        assert len(result.splitlines()) >= 1
