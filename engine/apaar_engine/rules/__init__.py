"""engine/apaar_engine/rules/__init__.py

Rules package and registry exports.
"""

# Import schema_rules to trigger rule registration
import apaar_engine.rules.schema_rules  # noqa: F401
from apaar_engine.rules.registry import (
    get_registered_rules,
    load_rule_catalog,
    register_rule,
    run_rule,
)

__all__ = [
    "get_registered_rules",
    "load_rule_catalog",
    "register_rule",
    "run_rule",
]
