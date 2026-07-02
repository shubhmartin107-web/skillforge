from __future__ import annotations

import time
from pathlib import Path

import yaml
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from skillforge._version import __version__
from skillforge.config import settings
from skillforge.models.registry import RegistryEntry, SearchQuery, SearchResult
from skillforge.models.skill import SkillManifest
from skillforge.registry.local import LocalRegistry

_start_time = time.monotonic()

app = FastAPI(
    title="SkillForge Registry Server",
    description="Remote skill registry for discovering and downloading agent skills",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "DELETE") and settings.server_api_keys:
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key not in settings.server_api_keys:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid or missing API key"},
                )
        response = await call_next(request)
        return response


app.add_middleware(APIKeyMiddleware)


@app.on_event("startup")
def startup():
    settings.ensure_dirs()


def get_registry() -> LocalRegistry:
    return LocalRegistry()


def verify_api_key(api_key: str | None) -> None:
    if settings.server_api_keys and (not api_key or api_key not in settings.server_api_keys):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


@app.get("/health")
def health():
    reg = get_registry()
    try:
        stats_result = reg.stats()
        skill_count = stats_result.total_skills
    finally:
        reg.close()
    return {
        "status": "ok",
        "version": __version__,
        "service": "skillforge-registry",
        "uptime_seconds": int(time.monotonic() - _start_time),
        "skills_count": skill_count,
    }


@app.get("/api/v1/skills", response_model=SearchResult)
def list_skills(
    query: str = Query("", description="Search query"),
    tag: str = Query("", description="Filter by tag"),
    category: str = Query("", description="Filter by category"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    reg = get_registry()
    sq = SearchQuery(
        query=query,
        tags=[tag] if tag else [],
        categories=[category] if category else [],
        offset=offset,
        limit=limit,
    )
    result = reg.search(sq)
    reg.close()
    return result


@app.get("/api/v1/skills/{name}", response_model=RegistryEntry | dict)
def get_skill(name: str, version: str | None = Query(None)):
    reg = get_registry()
    entry = reg.get(name, version)
    reg.close()
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return entry


@app.get("/api/v1/skills/{name}/download")
def download_skill(name: str, version: str | None = Query(None)):
    reg = get_registry()
    entry = reg.get(name, version)
    if entry is None:
        reg.close()
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    reg.increment_downloads(name, entry.version)

    import tempfile
    import zipfile

    skill_path = Path(entry.skill_path)
    if not skill_path.exists():
        reg.close()
        raise HTTPException(status_code=404, detail="Skill files not found")

    zip_path = Path(tempfile.mktemp(suffix=".zip"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_path.rglob("*"):
            if file_path.is_file():
                arcname = str(file_path.relative_to(skill_path))
                zf.write(file_path, arcname)

    reg.close()

    filename = f"{name}-{entry.version}.zip"
    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/v1/skills/{name}/download")
def track_download(name: str, version: str | None = Query(None)):
    reg = get_registry()
    entry = reg.get(name, version)
    if entry is None:
        reg.close()
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    actual_version = version or entry.version
    reg.increment_downloads(name, actual_version)

    updated = reg.get(name, actual_version)
    reg.close()

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated entry")

    return {
        "name": name,
        "version": actual_version,
        "download_url": f"/api/v1/skills/{name}/download?version={actual_version}",
        "total_downloads": updated.downloads,
    }


@app.post("/api/v1/skills/publish")
async def publish_skill(
    manifest: str = Form(...),
    files: list[UploadFile] = File(...),  # noqa: B008
):
    data = yaml.safe_load(manifest)
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid manifest format")
    manifest_obj = SkillManifest.from_yaml_dict(data)

    skill_dir = settings.skills_path / manifest_obj.name / manifest_obj.version
    skill_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        content = await file.read()
        filename = file.filename or "unknown"
        file_path = skill_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    manifest_path = skill_dir / "skill.yaml"
    manifest_path.write_text(manifest)

    size_bytes = sum(f.stat().st_size for f in skill_dir.rglob("*") if f.is_file())

    entry = RegistryEntry(
        name=manifest_obj.name,
        version=manifest_obj.version,
        description=manifest_obj.description,
        author_name=manifest_obj.author.name,
        tags=manifest_obj.tags,
        categories=manifest_obj.categories,
        source="remote",
        source_url="",
        manifest_path=str(manifest_path),
        skill_path=str(skill_dir),
        dependencies=[d.name for d in manifest_obj.dependencies],
        entrypoint=manifest_obj.execution.get("entrypoint", "skill.py"),
        execution_mode=manifest_obj.execution.get("mode", "direct"),
        size_bytes=size_bytes,
        downloads=0,
    )

    reg = get_registry()
    reg.install(entry)
    reg.close()

    return entry


@app.get("/api/v1/profile")
def profile(x_api_key: str | None = Header(None)):
    verify_api_key(x_api_key)
    return {
        "authenticated": True,
        "api_key": x_api_key[:8] + "..." if x_api_key and len(x_api_key) > 8 else x_api_key,
        "role": "admin",
    }


@app.delete("/api/v1/skills/{name}")
def delete_skill(name: str):
    reg = get_registry()
    entry = reg.get(name)
    if entry is None:
        reg.close()
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    skill_dir = Path(entry.skill_path)
    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)

    parent = skill_dir.parent
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()

    reg.remove(name)
    reg.close()
    return {"detail": f"Skill '{name}' deleted"}


@app.get("/api/v1/stats")
def stats():
    reg = get_registry()
    s = reg.stats()
    reg.close()
    return s


@app.get("/api/v1/index")
def registry_index():
    reg = get_registry()
    entries = reg.list_all()
    reg.close()
    return {
        "format": "skillforge-registry-v1",
        "total": len(entries),
        "skills": [
            {
                "name": e.name,
                "version": e.version,
                "description": e.description,
                "author": e.author_name,
                "tags": e.tags,
                "categories": e.categories,
                "downloads": e.downloads,
            }
            for e in entries
        ],
    }
