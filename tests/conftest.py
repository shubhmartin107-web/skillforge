from __future__ import annotations

from pathlib import Path

import pytest

from skillforge.models.skill import SkillManifest
from skillforge.registry.installer import Installer
from skillforge.registry.local import LocalRegistry


@pytest.fixture
def test_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def registry():
    reg = LocalRegistry(db_path=Path("/tmp/sf_test_registry.db"))
    yield reg
    reg.close()
    if reg.db_path.exists():
        reg.db_path.unlink()


@pytest.fixture
def installer(registry):
    return Installer(registry=registry)


@pytest.fixture
def sample_skill_manifest():
    return SkillManifest(
        name="test-skill",
        version="1.0.0",
        description="A test skill",
        inputs=[{"name": "input1", "type": "string", "required": True}],
        outputs=[{"name": "output1", "type": "string"}],
    )
