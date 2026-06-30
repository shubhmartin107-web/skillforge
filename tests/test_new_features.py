from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from skillforge._version import __version__
from skillforge.config import settings
from skillforge.models.skill import SkillManifest
from skillforge.registry.community import CommunityRegistry, CommunitySkill
from skillforge.registry.local import LocalRegistry
from skillforge.runtime.openapi import generate_openapi_spec, generate_openapi_yaml
from skillforge.runtime.wasm_sandbox import WasmSandbox, create_sandbox


class TestWasmSandbox:
    def test_wasm_sandbox_interface(self):
        sandbox = WasmSandbox()
        assert callable(getattr(sandbox, "execute_python", None))
        assert callable(getattr(sandbox, "prepare_skill", None))
        assert hasattr(WasmSandbox, "workdir")
        assert hasattr(sandbox, "__enter__")
        assert hasattr(sandbox, "__exit__")

    def test_create_sandbox_returns_sandbox(self):
        sb = create_sandbox(use_wasm=True)
        assert callable(getattr(sb, "execute_python", None))

    def test_create_sandbox_returns_subprocess_fallback(self):
        sb = create_sandbox(use_wasm=False)
        assert hasattr(sb, "execute_python")

    def test_wasm_sandbox_execute_simple_code(self):
        sandbox = WasmSandbox()
        with sandbox:
            result = sandbox.execute_python(
                "def run() -> dict:\n    return {'sum': 2 + 2}",
                function_name="run",
            )
        assert result.get("sum") == 4

    def test_wasm_sandbox_with_inputs(self):
        sandbox = WasmSandbox()
        with sandbox:
            result = sandbox.execute_python(
                "def run(a: int, b: int) -> dict:\n    return {'product': a * b}",
                function_name="run",
                inputs={"a": 3, "b": 7},
            )
        assert result.get("product") == 21

    def test_wasm_sandbox_timeout(self):
        sandbox = WasmSandbox(timeout=1)
        with sandbox:
            with pytest.raises(Exception):
                sandbox.execute_python(
                    "import time\ndef run() -> dict:\n    time.sleep(10)\n    return {}",
                    function_name="run",
                )

    def test_sandbox_cleanup_tempdir(self):
        sandbox = WasmSandbox()
        with sandbox:
            tmpdir = sandbox.workdir
            assert tmpdir.exists()
        assert not tmpdir.exists()

    def test_prepare_skill(self):
        with tempfile.TemporaryDirectory() as td:
            skill_dir = Path(td) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "skill.py").write_text("def run(): return {}")
            (skill_dir / "skill.yaml").write_text("name: test")

            sandbox = WasmSandbox()
            with sandbox:
                dest = sandbox.prepare_skill(skill_dir)
                assert dest.exists()
                assert (dest / "skill.py").exists()
                assert (dest / "skill.yaml").exists()


class TestOpenAPIGenerator:
    def test_generate_spec_from_manifest(self):
        manifest = SkillManifest(
            name="test-skill",
            version="1.0.0",
            description="A test skill",
            author={"name": "Test Author", "contact": "test@example.com"},
            inputs=[
                {"name": "message", "type": "string", "description": "Input message", "required": True},
                {"name": "count", "type": "integer", "description": "Count value", "required": False, "default": 42},
            ],
            outputs=[
                {"name": "result", "type": "string", "description": "Output result"},
            ],
            tags=["test", "example"],
            categories=["utility"],
            execution={"mode": "direct", "entrypoint": "skill.py", "function": "run"},
            license="MIT",
        )

        spec = generate_openapi_spec(manifest)
        assert spec["openapi"] == "3.0.3"
        assert "test-skill" in spec["info"]["title"]
        assert spec["info"]["version"] == "1.0.0"
        assert spec["info"]["description"] == "A test skill"
        assert "/skills/test-skill" in spec["paths"]

    def test_generate_spec_from_yaml_file(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "skill.yaml"
            manifest_path.write_text(yaml.dump({
                "name": "file-test",
                "version": "0.5.0",
                "description": "From file",
                "inputs": [{"name": "x", "type": "float", "description": "A number", "required": True}],
                "outputs": [{"name": "y", "type": "float", "description": "Result"}],
                "permissions": {"network": False},
                "execution": {"mode": "direct", "entrypoint": "skill.py", "function": "run"},
            }))
            spec = generate_openapi_spec(str(manifest_path))
            assert "file-test" in spec["info"]["title"]
            assert spec["info"]["version"] == "0.5.0"

    def test_generate_yaml_string(self):
        manifest = SkillManifest(
            name="yaml-test",
            version="2.0.0",
            description="YAML output test",
            execution={"mode": "direct", "entrypoint": "skill.py", "function": "run"},
        )
        yaml_str = generate_openapi_yaml(manifest)
        assert "openapi: 3.0.3" in yaml_str
        assert "yaml-test" in yaml_str

    def test_spec_has_request_body(self):
        manifest = SkillManifest(
            name="test-body",
            version="1.0.0",
            description="Test request body",
            inputs=[
                {"name": "name", "type": "string", "description": "Your name", "required": True},
                {"name": "age", "type": "integer", "description": "Your age", "required": False, "default": 0},
            ],
            outputs=[{"name": "greeting", "type": "string", "description": "Greeting"}],
            execution={"mode": "direct", "entrypoint": "skill.py", "function": "run"},
        )
        spec = generate_openapi_spec(manifest)
        path_item = spec["paths"]["/skills/test-body"]
        post_op = path_item.get("post")
        assert post_op is not None
        assert "requestBody" in post_op
        assert "application/json" in post_op["requestBody"]["content"]

    def test_spec_has_responses(self):
        manifest = SkillManifest(
            name="test-resp",
            version="1.0.0",
            description="Test responses",
            inputs=[{"name": "q", "type": "string", "description": "Query", "required": True}],
            outputs=[{"name": "answer", "type": "string", "description": "Answer"}],
            execution={"mode": "direct", "entrypoint": "skill.py", "function": "run"},
        )
        spec = generate_openapi_spec(manifest)
        post_op = spec["paths"]["/skills/test-resp"]["post"]
        assert "200" in post_op["responses"]
        assert "400" in post_op["responses"]
        assert "500" in post_op["responses"]


class TestCommunityRegistry:
    def test_community_skill_model(self):
        skill = CommunitySkill(
            name="test-community",
            version="1.0.0",
            description="A community skill",
            author="Community Author",
            downloads=42,
            categories=["utility"],
            tags=["test"],
            registry_url="https://community.skillforge.ai",
        )
        assert skill.name == "test-community"
        assert skill.downloads == 42
        assert "utility" in skill.categories

    def test_community_registry_init(self):
        cr = CommunityRegistry()
        assert cr.base_url == settings.community_registry_url

    def test_community_registry_custom_url(self):
        cr = CommunityRegistry(base_url="https://custom.example.com")
        assert cr.base_url == "https://custom.example.com"

    def test_community_registry_discover_no_server(self):
        cr = CommunityRegistry(base_url="http://localhost:1")
        with pytest.raises(Exception):
            cr.discover()

    def test_community_registry_install_no_server(self):
        cr = CommunityRegistry(base_url="http://localhost:1")
        with pytest.raises(Exception):
            cr.install_from_community("nonexistent-skill")

    def test_community_registry_submit_no_server(self):
        cr = CommunityRegistry(base_url="http://localhost:1")
        with tempfile.TemporaryDirectory() as td:
            skill_dir = Path(td) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "skill.yaml").write_text(yaml.dump({
                "name": "test-skill",
                "version": "0.1.0",
                "execution": {"mode": "direct"},
            }))
            with pytest.raises(Exception):
                cr.submit_skill(skill_dir, "test-key")


class TestServerUpgrade:
    def test_registry_entry_has_downloads(self):
        from skillforge.models.registry import RegistryEntry
        entry = RegistryEntry(
            name="test-downloads",
            version="1.0.0",
            description="Test downloads tracking",
            author_name="Tester",
        )
        assert hasattr(entry, "downloads")
        assert entry.downloads == 0

    def test_server_health_endpoint(self):
        from skillforge.registry.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == __version__

    def test_server_skills_endpoint(self):
        from skillforge.registry.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data

    def test_server_stats_endpoint(self):
        from skillforge.registry.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/v1/stats")
        assert response.status_code == 200

    def test_server_index_endpoint(self):
        from skillforge.registry.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/v1/index")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "skillforge-registry-v1"

    def test_server_profile_no_auth(self):
        from skillforge.registry.server import app
        from skillforge.config import settings as settings_mod
        from fastapi.testclient import TestClient
        old_keys = settings_mod.server_api_keys
        settings_mod.server_api_keys = ["test-key"]
        try:
            client = TestClient(app)
            response = client.get("/api/v1/profile")
            assert response.status_code == 403
        finally:
            settings_mod.server_api_keys = old_keys

    def test_server_publish_no_auth(self):
        import io
        import zipfile

        from skillforge.registry.server import app
        from skillforge.config import settings as settings_mod
        from fastapi.testclient import TestClient

        old_keys = settings_mod.server_api_keys
        settings_mod.server_api_keys = ["test-key"]
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("skill.py", "def run(): return {}")
            manifest_data = yaml.dump({
                "name": "test", "version": "1.0.0",
                "execution": {"mode": "direct", "entrypoint": "skill.py", "function": "run"},
            })
            client = TestClient(app)
            response = client.post(
                "/api/v1/skills/publish",
                data={"manifest": manifest_data},
                files={"files": ("skill.zip", zip_buffer.getvalue(), "application/zip")},
            )
            assert response.status_code == 403
        finally:
            settings_mod.server_api_keys = old_keys

    def test_server_delete_no_auth(self):
        from skillforge.registry.server import app
        from skillforge.config import settings as settings_mod
        from fastapi.testclient import TestClient
        old_keys = settings_mod.server_api_keys
        settings_mod.server_api_keys = ["test-key"]
        try:
            client = TestClient(app)
            response = client.delete("/api/v1/skills/test-skill")
            assert response.status_code == 403
        finally:
            settings_mod.server_api_keys = old_keys


class TestPublishCLI:
    def test_publish_help(self):
        from typer.testing import CliRunner
        from skillforge.cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["registry", "publish", "--help"])
        assert result.exit_code == 0
        assert "PATH" in result.stdout

    def test_login_help(self):
        from typer.testing import CliRunner
        from skillforge.cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["registry", "login", "--help"])
        assert result.exit_code == 0

    def test_publish_no_path(self):
        from typer.testing import CliRunner
        from skillforge.cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["registry", "publish"])
        assert result.exit_code != 0

    def test_community_discover_help(self):
        from typer.testing import CliRunner
        from skillforge.cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["registry", "community", "--help"])
        assert result.exit_code == 0
        assert "discover" in result.stdout


class TestOpenAPICLI:
    def test_openapi_help(self):
        from typer.testing import CliRunner
        from skillforge.cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["skill", "openapi", "--help"])
        assert result.exit_code == 0

    def test_openapi_with_manifest_path(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "skill.yaml"
            manifest_path.write_text(yaml.dump({
                "name": "cli-openapi-test",
                "version": "1.0.0",
                "description": "CLI OpenAPI test",
                "inputs": [{"name": "x", "type": "integer", "description": "Input value", "required": True}],
                "outputs": [{"name": "y", "type": "integer", "description": "Output value"}],
                "execution": {"mode": "direct", "entrypoint": "skill.py", "function": "run"},
            }))
            from typer.testing import CliRunner
            from skillforge.cli.main import app
            runner = CliRunner()
            result = runner.invoke(app, ["skill", "openapi", str(manifest_path)])
            assert result.exit_code == 0
            assert "openapi: 3.0.3" in result.stdout

    def test_openapi_json_format(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "skill.yaml"
            manifest_path.write_text(yaml.dump({
                "name": "json-test",
                "version": "0.1.0",
                "execution": {"mode": "direct"},
            }))
            from typer.testing import CliRunner
            from skillforge.cli.main import app
            runner = CliRunner()
            result = runner.invoke(app, ["skill", "openapi", str(manifest_path), "--format", "json"])
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["openapi"] == "3.0.3"

    def test_openapi_with_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "skill.yaml"
            manifest_path.write_text(yaml.dump({
                "name": "output-test",
                "version": "0.1.0",
                "execution": {"mode": "direct"},
            }))
            output_path = Path(td) / "spec.yaml"
            from typer.testing import CliRunner
            from skillforge.cli.main import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "skill", "openapi", str(manifest_path),
                "--output", str(output_path),
            ])
            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            assert "openapi: 3.0.3" in content

    def test_openapi_from_installed_skill(self):
        with tempfile.TemporaryDirectory() as td:
            skill_dir = Path(td) / "installed-test"
            skill_dir.mkdir()
            manifest = {
                "name": "installed-openapi",
                "version": "1.0.0",
                "description": "Installed OpenAPI test",
                "inputs": [{"name": "inp", "type": "string", "description": "Input", "required": True}],
                "outputs": [{"name": "out", "type": "string", "description": "Output"}],
                "execution": {"mode": "direct", "entrypoint": "skill.py", "function": "run"},
            }
            (skill_dir / "skill.yaml").write_text(yaml.dump(manifest))
            (skill_dir / "skill.py").write_text("def run(inp: str) -> dict:\n    return {'out': inp}")

            reg = LocalRegistry()
            from skillforge.registry.installer import Installer
            installer = Installer()
            installer.install_from_path(skill_dir)
            reg.close()

            from typer.testing import CliRunner
            from skillforge.cli.main import app
            runner = CliRunner()
            result = runner.invoke(app, ["skill", "openapi", "installed-openapi"])
            assert result.exit_code == 0
            assert "installed-openapi" in result.stdout

            installer.remove("installed-openapi")
