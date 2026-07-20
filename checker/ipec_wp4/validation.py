from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v0.1"

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    registry = Registry()
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        schemas[schema["$id"]] = schema
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry, schemas

def validate_instance(instance: Any, schema_id: str) -> list[str]:
    registry, schemas = schema_registry()
    validator = Draft202012Validator(schemas[schema_id], registry=registry, format_checker=FormatChecker())
    return sorted(error.message for error in validator.iter_errors(instance))
