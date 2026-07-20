from __future__ import annotations
import copy, hashlib, json
from typing import Any

PROFILE_ID = "V0-IPEC-CJ-1"

def _reject_floats(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise ValueError(f"V0-IPEC-CJ-1 forbids floating-point values at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"JSON object key is not a string at {path}")
            _reject_floats(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_floats(child, f"{path}[{index}]")

def canonical_bytes(value: Any) -> bytes:
    _reject_floats(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def digest_view(envelope: dict[str, Any]) -> dict[str, Any]:
    view = copy.deepcopy(envelope)
    integrity = view.setdefault("integrity", {})
    integrity.pop("canonical_sha256", None)
    integrity.pop("canonical_size_bytes", None)
    return view

def compute_envelope_digest(envelope: dict[str, Any]) -> tuple[str, int]:
    data = canonical_bytes(digest_view(envelope))
    return hashlib.sha256(data).hexdigest(), len(data)

def seal_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(envelope)
    digest, size = compute_envelope_digest(sealed)
    sealed["integrity"]["canonical_sha256"] = digest
    sealed["integrity"]["canonical_size_bytes"] = size
    return sealed

def verify_envelope_digest(envelope: dict[str, Any]) -> bool:
    digest, size = compute_envelope_digest(envelope)
    return envelope.get("integrity", {}).get("canonical_sha256") == digest and envelope.get("integrity", {}).get("canonical_size_bytes") == size
