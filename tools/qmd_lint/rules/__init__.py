"""Importing this package registers every rule via the @rule decorator."""

from . import (  # noqa: F401
    link_rules,
    math_rules,
    note_rules,
    obsidian_rules,
    structure_rules,
    table_rules,
    yaml_rules,
)
