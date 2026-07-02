from __future__ import annotations

from skillforge.models.skill import SkillDependency
from skillforge.registry.local import LocalRegistry


class ResolutionError(Exception):
    pass


class DependencyResolver:
    def __init__(self, registry: LocalRegistry):
        self.registry = registry

    def resolve(self, dependencies: list[SkillDependency]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        self._resolve_many(dependencies, resolved, set())
        return resolved

    def _resolve_many(
        self,
        deps: list[SkillDependency],
        resolved: dict[str, str],
        visiting: set[str],
    ) -> None:
        for dep in deps:
            if dep.name in resolved:
                continue
            if dep.name in visiting:
                raise ResolutionError(f"Circular dependency detected: {dep.name}")
            visiting.add(dep.name)

            versions = self.registry.list_versions(dep.name)
            if not versions:
                raise ResolutionError(f"Dependency not found: {dep.name}")

            if dep.version == "*":
                best = versions[0]
            else:
                best = self._match_version(versions, dep.version)
                if best is None:
                    raise ResolutionError(
                        f"No version of '{dep.name}' matches constraint '{dep.version}'"
                    )

            resolved[dep.name] = best.version
            self._resolve_many(
                [SkillDependency(name=d, version="*") for d in best.dependencies],
                resolved,
                visiting,
            )
            visiting.remove(dep.name)

    def _match_version(self, versions, constraint: str) -> None:
        import semver

        try:
            constraint_ver = semver.Version.parse(constraint.replace("^", "").replace("~", ""))
        except ValueError:
            for v in versions:
                try:
                    sv = semver.Version.parse(v.version)
                except ValueError:
                    continue
                if constraint.startswith(">="):
                    if sv >= constraint_ver:
                        return v
                elif constraint.startswith("<="):
                    if sv <= constraint_ver:
                        return v
                elif constraint.startswith("^"):
                    if sv.major == constraint_ver.major and sv >= constraint_ver:
                        return v
                elif constraint.startswith("~") and (
                    sv.major == constraint_ver.major
                    and sv.minor == constraint_ver.minor
                    and sv >= constraint_ver
                ):
                    return v
            return None

        for v in versions:
            try:
                sv = semver.Version.parse(v.version)
            except ValueError:
                continue
            if constraint.startswith(">="):
                if sv >= constraint_ver:
                    return v
            elif constraint.startswith("<="):
                if sv <= constraint_ver:
                    return v
            elif constraint.startswith("^"):
                if sv.major == constraint_ver.major and sv >= constraint_ver:
                    return v
            elif constraint.startswith("~"):
                if (
                    sv.major == constraint_ver.major
                    and sv.minor == constraint_ver.minor
                    and sv >= constraint_ver
                ):
                    return v
            elif sv == constraint_ver:
                return v
        return None

    def _match_version(self, versions, constraint: str):
        import semver

        def parse_safe(v: str):
            try:
                return semver.Version.parse(v)
            except ValueError:
                return None

        sv_versions = [(v, parse_safe(v.version)) for v in versions]
        sv_versions = [(v, sv) for v, sv in sv_versions if sv is not None]
        sv_versions.sort(key=lambda x: x[1], reverse=True)

        if constraint == "*":
            return sv_versions[0][0] if sv_versions else None

        try:
            constraint_ver = semver.Version.parse(constraint.lstrip("^~>=<"))
        except ValueError:
            return None

        for entry, sv in sv_versions:
            if constraint.startswith(">="):
                if sv >= constraint_ver:
                    return entry
            elif constraint.startswith("<="):
                if sv <= constraint_ver:
                    return entry
            elif constraint.startswith("^"):
                if sv.major == constraint_ver.major and sv >= constraint_ver:
                    return entry
            elif constraint.startswith("~"):
                if (
                    sv.major == constraint_ver.major
                    and sv.minor == constraint_ver.minor
                    and sv >= constraint_ver
                ):
                    return entry
            elif sv == constraint_ver:
                return entry

        return None
