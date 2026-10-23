"""engine/apaar_engine/rules/registry.py

Validation rule registry that loads contracts/rule_catalog.yaml
and maps rule_id -> validation function.

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import yaml

from apaar_engine.models import Issue

RuleFunction = Callable[[pd.DataFrame, Dict[str, Any]], List[Issue]]

_RULE_REGISTRY: Dict[str, RuleFunction] = {}
_CATALOG_CACHE: Optional[Dict[str, Any]] = None


def get_rule_catalog_path() -> Path:
    """Find contracts/rule_catalog.yaml from workspace or package."""
    # 1. Search relative to repository root
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "contracts" / "rule_catalog.yaml"
    if candidate.exists():
        return candidate

    # 2. Search parent dirs
    curr = Path(__file__).resolve()
    for _ in range(5):
        curr = curr.parent
        candidate = curr / "contracts" / "rule_catalog.yaml"
        if candidate.exists():
            return candidate

    raise FileNotFoundError("contracts/rule_catalog.yaml could not be found.")


def load_rule_catalog() -> Dict[str, Any]:
    """Load and cache contracts/rule_catalog.yaml."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        path = get_rule_catalog_path()
        with open(path, "r", encoding="utf-8") as f:
            _CATALOG_CACHE = yaml.safe_load(f)
    return _CATALOG_CACHE


def register_rule(rule_id: str) -> Callable[[RuleFunction], RuleFunction]:
    """Decorator to register a validation rule function by rule ID."""
    def decorator(fn: RuleFunction) -> RuleFunction:
        _RULE_REGISTRY[rule_id] = fn
        return fn
    return decorator


def get_registered_rules() -> Dict[str, RuleFunction]:
    """Return all registered rule functions."""
    return dict(_RULE_REGISTRY)


def run_rule(
    rule_id: str,
    df: pd.DataFrame,
    catalog: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> List[Issue]:
    """Run a single registered rule if present."""
    if rule_id not in _RULE_REGISTRY:
        return []

    if catalog is None:
        catalog = load_rule_catalog()

    rule_meta = {}
    for r in catalog.get("rules", []):
        if r.get("id") == rule_id:
            rule_meta = r
            break

    return _RULE_REGISTRY[rule_id](df, rule_meta, **kwargs)
