from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx
import yaml

from skillforge.models.skill import SkillManifest


class RemoteRegistry:
    GITHUB_API = "https://api.github.com"

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0, follow_redirects=True)
        return self._client

    def fetch_index(self, url: str) -> list[dict[str, Any]]:
        resp = self.client.get(url)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("skills", data.get("entries", []))
        return []

    def fetch_from_github(self, repo: str, path: str = "") -> list[dict[str, Any]]:
        api_url = f"{self.GITHUB_API}/repos/{repo}/contents/{path}"
        resp = self.client.get(api_url)
        resp.raise_for_status()
        items = resp.json()

        skills: list[dict[str, Any]] = []
        for item in items if isinstance(items, list) else [items]:
            if item.get("type") == "file" and item["name"] in ("skill.yaml", "skill.yml", "skill.json"):
                file_resp = self.client.get(item["download_url"])
                file_resp.raise_for_status()
                content = file_resp.text
                try:
                    if item["name"].endswith(".json"):
                        data = json.loads(content)
                    else:
                        data = yaml.safe_load(content)
                    skills.append(data)
                except (json.JSONDecodeError, yaml.YAMLError):
                    continue
            elif item.get("type") == "dir":
                skills.extend(self.fetch_from_github(repo, item["path"]))
        return skills

    def download_skill(self, url: str, dest: Path) -> SkillManifest | None:
        resp = self.client.get(url)
        resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(resp.content)
            zip_path = f.name

        manifest = None
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(dest)
                for name in zf.namelist():
                    if Path(name).name in ("skill.yaml", "skill.yml", "skill.json"):
                        content = zf.read(name).decode("utf-8")
                        if name.endswith(".json"):
                            data = json.loads(content)
                        else:
                            data = yaml.safe_load(content)
                        manifest = SkillManifest.from_yaml_dict(data)
                        break
        finally:
            Path(zip_path).unlink(missing_ok=True)

        return manifest

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
