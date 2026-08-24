"""Run Bundle deny-list scan applied after strict schema validation."""

from __future__ import annotations

import re

from packages.contracts.models import RunBundle
from packages.contracts.run_bundle import RunBundleV2

_FORBIDDEN_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "mainland_phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "api_key": re.compile(r"\b(?:sk|key|token)[-_][A-Za-z0-9]{16,}\b", re.IGNORECASE),
    "private_key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "absolute_path": re.compile(
        r"(?:/(?:Users|home)/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)"
    ),
}


def assert_bundle_safe(bundle: RunBundle | RunBundleV2) -> None:
    serialized = bundle.model_dump_json()
    matches = [name for name, pattern in _FORBIDDEN_PATTERNS.items() if pattern.search(serialized)]
    if matches:
        raise ValueError(f"Run bundle contains forbidden patterns: {', '.join(matches)}")
