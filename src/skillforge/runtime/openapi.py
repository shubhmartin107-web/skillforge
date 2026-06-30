from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from skillforge.models.skill import SkillManifest
from skillforge.registry.local import LocalRegistry

TYPE_MAP: dict[str, dict[str, Any]] = {
    "string": {"type": "string"},
    "integer": {"type": "integer"},
    "float": {"type": "number", "format": "float"},
    "boolean": {"type": "boolean"},
    "list": {"type": "array", "items": {"type": "string"}},
    "object": {"type": "object"},
    "any": {},
}


def _resolve_manifest(manifest_or_path: SkillManifest | str | Path) -> SkillManifest:
    if isinstance(manifest_or_path, SkillManifest):
        return manifest_or_path

    path = Path(manifest_or_path)
    if path.exists():
        raw = yaml.safe_load(path.read_text("utf-8"))
        return SkillManifest.from_yaml_dict(raw)

    registry = LocalRegistry()
    entry = registry.get(str(manifest_or_path))
    if entry is None:
        raise ValueError(f"Skill '{manifest_or_path}' not found in registry")
    manifest_path = Path(entry.manifest_path)
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")
    raw = yaml.safe_load(manifest_path.read_text("utf-8"))
    return SkillManifest.from_yaml_dict(raw)


def _build_schema_from_manifest(manifest: SkillManifest) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for inp in manifest.inputs:
        prop = dict(TYPE_MAP.get(inp.type, {"type": "string"}))
        if inp.description:
            prop["description"] = inp.description
        if inp.default is not None:
            prop["default"] = inp.default

        example = _find_example(manifest, inp.name)
        if example is not None:
            prop["example"] = example

        properties[inp.name] = prop
        if inp.required:
            required.append(inp.name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


def _find_example(manifest: SkillManifest, input_name: str) -> Any:
    for example in manifest.examples:
        if isinstance(example, dict) and input_name in example:
            return example[input_name]
    return None


def _build_response_schema(manifest: SkillManifest) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for out in manifest.outputs:
        prop = dict(TYPE_MAP.get(out.type, {"type": "string"}))
        if out.description:
            prop["description"] = out.description
        properties[out.name] = prop

    if not properties:
        return {"type": "object", "properties": {"result": {"type": "string"}}}

    return {"type": "object", "properties": properties}


def generate_openapi_spec(manifest_or_path: SkillManifest | str | Path) -> dict[str, Any]:
    manifest = _resolve_manifest(manifest_or_path)

    path_name = f"/skills/{manifest.name}"
    input_schema = _build_schema_from_manifest(manifest)
    response_schema = _build_response_schema(manifest)

    tags = list(dict.fromkeys(manifest.tags + manifest.categories)) or [manifest.name]

    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": f"{manifest.name} — SkillForge API",
            "version": manifest.version,
            "description": manifest.description
            or f"Auto-generated OpenAPI spec for {manifest.name}",
        },
        "paths": {
            path_name: {
                "post": {
                    "summary": f"Execute {manifest.name}",
                    "description": manifest.description or f"Execute the {manifest.name} skill",
                    "operationId": f"execute_{manifest.name.replace('-', '_').replace('.', '_')}",
                    "tags": tags,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": input_schema,
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Successful execution",
                            "content": {
                                "application/json": {
                                    "schema": response_schema,
                                }
                            },
                        },
                        "400": {
                            "description": "Bad request — invalid input",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "500": {
                            "description": "Internal error during skill execution",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                    },
                }
            }
        },
    }

    if manifest.author and manifest.author.name != "Unknown":
        spec["info"]["contact"] = {
            "name": manifest.author.name,
        }
        if manifest.author.contact:
            spec["info"]["contact"]["url"] = manifest.author.contact

    if manifest.permissions and manifest.permissions.env_vars:
        spec["components"] = {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": f"Required env vars: {', '.join(manifest.permissions.env_vars)}",
                }
            }
        }
        spec["security"] = [{"ApiKeyAuth": []}]

    if manifest.license:
        spec["info"]["license"] = {"name": manifest.license}

    if manifest.examples:
        spec["info"]["description"] = (spec["info"]["description"] + "\n\n### Examples\n" +
                                       "\n".join(f"- `{json.dumps(e)}`" for e in manifest.examples))

    return spec


def generate_openapi_yaml(
    manifest_or_path: SkillManifest | str | Path,
    output_file: str | Path | None = None,
) -> str:
    spec = generate_openapi_spec(manifest_or_path)
    yaml_str = yaml.dump(spec, default_flow_style=False, sort_keys=False, allow_unicode=True)
    if output_file:
        Path(output_file).write_text(yaml_str, "utf-8")
    return yaml_str


def generate_openapi_json(
    manifest_or_path: SkillManifest | str | Path,
    output_file: str | Path | None = None,
) -> str:
    spec = generate_openapi_spec(manifest_or_path)
    json_str = json.dumps(spec, indent=2)
    if output_file:
        Path(output_file).write_text(json_str, "utf-8")
    return json_str


def serve_openapi_spec(
    manifest_or_path: SkillManifest | str | Path,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    spec = generate_openapi_spec(manifest_or_path)

    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError as e:
        raise ImportError(
            "FastAPI and uvicorn are required to serve the OpenAPI spec. "
            "Install them with: pip install skillforge[server]"
        ) from e

    app = FastAPI(
        title=spec["info"]["title"],
        description=spec["info"].get("description", ""),
        version=spec["info"]["version"],
    )

    swagger_html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{spec['info']['title']}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({{
      url: '/openapi.json',
      dom_id: '#swagger-ui',
    }});
  </script>
</body>
</html>"""

    @app.get("/openapi.json", include_in_schema=False)
    async def get_spec() -> JSONResponse:
        return JSONResponse(spec)

    @app.get("/", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        return HTMLResponse(swagger_html)

    print(f"Serving OpenAPI spec for {spec['info']['title']} at http://{host}:{port}")
    print(f"Swagger UI: http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port)
