"""engine/apaar_engine/rules/__init__.py

Rules package and registry exports.
"""

import apaar_engine.rules.consistency_rules  # noqa: F401
import apaar_engine.rules.intake_rules  # noqa: F401
import apaar_engine.rules.registry_rules  # noqa: F401

# Trigger rule registrations across modules
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
