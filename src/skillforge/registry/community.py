from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from skillforge.config import settings
from skillforge.models.registry import RegistryEntry


class CommunitySkill(BaseModel):
    name: str
    version: str
    description: str = ""
    author: str = ""
    downloads: int = 0
    rating: float = 0.0
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    registry_url: str = ""


class CommunityRegistry:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.community_registry_url
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0, follow_redirects=True)
        return self._client

    def discover(self) -> list[CommunitySkill]:
        resp = self.client.get(f"{self.base_url}/api/v1/index")
        resp.raise_for_status()
        data = resp.json()
        skills = data.get("skills", [])
        return [CommunitySkill(**s, registry_url=self.base_url) for s in skills]

    def install_from_community(self, name: str) -> RegistryEntry:
        resp = self.client.get(f"{self.base_url}/api/v1/skills/{name}/download")
        resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(resp.content)
            zip_path = f.name

        try:
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            from skillforge.registry.installer import Installer

            installer = Installer()
            entry = installer.install_from_path(extract_dir)
            return entry
        finally:
            Path(zip_path).unlink(missing_ok=True)
            shutil.rmtree(extract_dir, ignore_errors=True)

    def submit_skill(self, path: Path, api_key: str) -> dict[str, Any]:
        path = Path(path).resolve()
        if not path.exists():
            raise ValueError(f"Path not found: {path}")

        if path.is_file() and path.suffix == ".zip":
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_dir)
            source_dir = extract_dir
            cleanup_extract = True
        else:
            source_dir = path
            cleanup_extract = False

        try:
            manifest_path = source_dir / "skill.yaml"
            if not manifest_path.exists():
                raise ValueError("No skill.yaml found in skill directory")
            manifest_content = manifest_path.read_text("utf-8")

            files_list: list[tuple[str, tuple[str, bytes, str]]] = []
            for f in source_dir.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(source_dir)
                    files_list.append(
                        ("files", (str(rel), f.read_bytes(), "application/octet-stream"))
                    )

            headers = {"X-API-Key": api_key}
            data = {"manifest": manifest_content}

            resp = self.client.post(
                f"{self.base_url}/api/v1/skills/publish",
                data=data,
                files=files_list,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
        finally:
            if cleanup_extract:
                shutil.rmtree(source_dir, ignore_errors=True)

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
