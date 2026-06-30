from __future__ import annotations

from pathlib import Path

from skillforge.models.registry import SearchQuery


class TestLocalRegistry:
    def test_install_and_get(self, registry, sample_skill_manifest):
        from skillforge.models.registry import RegistryEntry

        entry = RegistryEntry(
            name=sample_skill_manifest.name,
            version=sample_skill_manifest.version,
            description=sample_skill_manifest.description,
            tags=["test"],
        )
        registry.install(entry)

        retrieved = registry.get("test-skill")
        assert retrieved is not None
        assert retrieved.name == "test-skill"
        assert retrieved.version == "1.0.0"

    def test_search(self, registry):
        from skillforge.models.registry import RegistryEntry

        for i in range(3):
            registry.install(RegistryEntry(
                name=f"skill-{i}",
                version=f"1.{i}.0",
                description=f"Test skill {i}",
                tags=["test"],
            ))

        result = registry.search(SearchQuery(query="skill"))
        assert result.total == 3

        result = registry.search(SearchQuery(query="skill", tags=["test"]))
        assert result.total == 3

    def test_remove(self, registry):
        from skillforge.models.registry import RegistryEntry
        registry.install(RegistryEntry(name="temp", version="1.0.0"))
        assert registry.get("temp") is not None
        registry.remove("temp")
        assert registry.get("temp") is None

    def test_stats(self, registry):
        from skillforge.models.registry import RegistryEntry
        registry.install(RegistryEntry(name="a", version="1.0.0", tags=["x"]))
        registry.install(RegistryEntry(name="b", version="1.0.0", tags=["y"]))

        stats = registry.stats()
        assert stats.total_skills == 2


class TestInstaller:
    def test_install_from_path(self, installer, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text("""
name: my-skill
version: 1.0.0
description: Test
tags: [test]
""")
        (skill_dir / "skill.py").write_text("def run(): return {}")

        entry = installer.install_from_path(skill_dir)
        assert entry.name == "my-skill"
        assert entry.version == "1.0.0"

        retrieved = installer.registry.get("my-skill")
        assert retrieved is not None
        assert retrieved.name == "my-skill"

    def test_remove(self, installer, tmp_path):
        skill_dir = tmp_path / "to-remove"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text("name: to-remove\nversion: 1.0.0\n")
        (skill_dir / "skill.py").write_text("def run(): return {}")

        entry = installer.install_from_path(skill_dir)
        assert entry is not None

        result = installer.remove("to-remove")
        assert result
        assert installer.registry.get("to-remove") is None
