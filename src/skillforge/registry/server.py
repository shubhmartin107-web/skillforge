from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from skillforge._version import __version__
from skillforge.config import settings
from skillforge.models.registry import RegistryEntry, SearchQuery, SearchResult
from skillforge.registry.local import LocalRegistry

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


@app.on_event("startup")
def startup():
    settings.ensure_dirs()


def get_registry() -> LocalRegistry:
    return LocalRegistry()


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "service": "skillforge-registry"}


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
    reg.close()
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    import tempfile
    import zipfile

    skill_path = Path(entry.skill_path)
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill files not found")

    zip_path = Path(tempfile.mktemp(suffix=".zip"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_path.rglob("*"):
            if file_path.is_file():
                arcname = str(file_path.relative_to(skill_path))
                zf.write(file_path, arcname)

    filename = f"{name}-{entry.version}.zip"
    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
            }
            for e in entries
        ],
    }
