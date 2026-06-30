from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from skillforge.config import settings
from skillforge.models.registry import RegistryEntry, RegistryStats, SearchQuery, SearchResult


class LocalRegistry:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or settings.registry_path
        settings.ensure_dirs()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT DEFAULT '',
                author_name TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                categories TEXT DEFAULT '[]',
                installed_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                source TEXT DEFAULT 'local',
                source_url TEXT DEFAULT '',
                manifest_path TEXT DEFAULT '',
                skill_path TEXT DEFAULT '',
                dependencies TEXT DEFAULT '[]',
                entrypoint TEXT DEFAULT '',
                execution_mode TEXT DEFAULT 'direct',
                size_bytes INTEGER DEFAULT 0,
                PRIMARY KEY (name, version)
            );
            CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
            CREATE INDEX IF NOT EXISTS idx_skills_tags ON skills(tags);
            CREATE INDEX IF NOT EXISTS idx_skills_categories ON skills(categories);
        """)

    def install(self, entry: RegistryEntry) -> None:
        data = entry.to_dict()
        data["installed_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        data["tags"] = json.dumps(data.get("tags", []))
        data["categories"] = json.dumps(data.get("categories", []))
        data["dependencies"] = json.dumps(data.get("dependencies", []))

        self.conn.execute("""
            INSERT OR REPLACE INTO skills
                (name, version, description, author_name, tags, categories,
                 installed_at, updated_at, source, source_url,
                 manifest_path, skill_path, dependencies, entrypoint,
                 execution_mode, size_bytes)
            VALUES
                (:name, :version, :description, :author_name, :tags, :categories,
                 :installed_at, :updated_at, :source, :source_url,
                 :manifest_path, :skill_path, :dependencies, :entrypoint,
                 :execution_mode, :size_bytes)
        """, data)
        self.conn.commit()

    def remove(self, name: str, version: str | None = None) -> bool:
        if version:
            cursor = self.conn.execute("DELETE FROM skills WHERE name = ? AND version = ?", (name, version))
        else:
            cursor = self.conn.execute("DELETE FROM skills WHERE name = ?", (name,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get(self, name: str, version: str | None = None) -> RegistryEntry | None:
        if version:
            row = self.conn.execute(
                "SELECT * FROM skills WHERE name = ? AND version = ?", (name, version)
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT * FROM skills WHERE name = ? ORDER BY installed_at DESC LIMIT 1", (name,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def list_all(self) -> list[RegistryEntry]:
        rows = self.conn.execute(
            "SELECT * FROM skills ORDER BY name, installed_at DESC"
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def list_versions(self, name: str) -> list[RegistryEntry]:
        rows = self.conn.execute(
            "SELECT * FROM skills WHERE name = ? ORDER BY version DESC", (name,)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def search(self, query: SearchQuery) -> SearchResult:
        conditions: list[str] = []
        params: list[Any] = []

        if query.query:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{query.query}%", f"%{query.query}%"])

        if query.tags:
            for tag in query.tags:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")

        if query.categories:
            for cat in query.categories:
                conditions.append("categories LIKE ?")
                params.append(f"%{cat}%")

        if query.author:
            conditions.append("author_name = ?")
            params.append(query.author)

        if query.mode:
            conditions.append("execution_mode = ?")
            params.append(query.mode)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        count_row = self.conn.execute(f"SELECT COUNT(*) as cnt FROM skills {where}", params).fetchone()
        total = count_row["cnt"] if count_row else 0

        rows = self.conn.execute(
            f"SELECT * FROM skills {where} ORDER BY name LIMIT ? OFFSET ?",
            params + [query.limit, query.offset]
        ).fetchall()

        return SearchResult(
            entries=[self._row_to_entry(r) for r in rows],
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def stats(self) -> RegistryStats:
        row = self.conn.execute("""
            SELECT
                COUNT(*) as total_skills,
                COUNT(DISTINCT name) as unique_skills
            FROM skills
        """).fetchone()

        tags_row = self.conn.execute("SELECT tags FROM skills").fetchall()
        all_tags: set[str] = set()
        for r in tags_row:
            import json
            try:
                all_tags.update(json.loads(r["tags"]))
            except (json.JSONDecodeError, TypeError):
                pass

        all_categories: set[str] = set()
        for r in self.conn.execute("SELECT categories FROM skills").fetchall():
            import json
            try:
                all_categories.update(json.loads(r["categories"]))
            except (json.JSONDecodeError, TypeError):
                pass

        authors = self.conn.execute("SELECT COUNT(DISTINCT author_name) as cnt FROM skills").fetchone()

        return RegistryStats(
            total_skills=row["total_skills"] if row else 0,
            total_categories=len(all_categories),
            total_tags=len(all_tags),
            total_authors=authors["cnt"] if authors else 0,
            last_updated=datetime.now(),
        )

    def _row_to_entry(self, row: sqlite3.Row) -> RegistryEntry:
        return RegistryEntry(
            name=row["name"],
            version=row["version"],
            description=row["description"],
            author_name=row["author_name"],
            tags=json.loads(row["tags"] or "[]"),
            categories=json.loads(row["categories"] or "[]"),
            installed_at=datetime.fromisoformat(row["installed_at"]) if row["installed_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            source=row["source"],
            source_url=row["source_url"],
            manifest_path=row["manifest_path"],
            skill_path=row["skill_path"],
            dependencies=json.loads(row["dependencies"] or "[]"),
            entrypoint=row["entrypoint"],
            execution_mode=row["execution_mode"],
            size_bytes=row["size_bytes"],
        )

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
