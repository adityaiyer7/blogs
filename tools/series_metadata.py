"""Dependency-free parsing and validation for flat blog-series metadata.

Quarto's listing injector runs under plain ``python3``, so it cannot depend on
PyYAML being installed.  Series metadata deliberately has a much smaller
contract than arbitrary YAML: three top-level, single-line scalar fields.  This
module parses that contract once so rendering and qmd_lint enforce identical
rules.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


SERIES_KEYS = ("series-id", "series", "series-order")

_FIELD_RE = re.compile(r"^(series-id|series|series-order):(?:[ \t]*(.*))?$")
_SERIES_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_INTEGER_RE = re.compile(r"^[+-]?\d+$")
_NON_STRING_PLAIN_SCALARS = {
    "null",
    "~",
    "true",
    "false",
    "yes",
    "no",
    "on",
    "off",
}


@dataclass(frozen=True)
class SeriesMetadata:
    """Validated metadata for one series member."""

    series_id: str
    title: str
    order: int


@dataclass(frozen=True)
class SeriesMetadataError:
    """One author-facing metadata contract violation."""

    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


def _comment_start(value: str) -> int | None:
    """Return the first YAML-style comment marker outside a quoted scalar."""
    for index, char in enumerate(value):
        if char == "#" and (index == 0 or value[index - 1].isspace()):
            return index
    return None


def _trailing_is_comment(remainder: str) -> bool:
    remainder = remainder.strip()
    return not remainder or remainder.startswith("#")


def _parse_single_quoted(value: str) -> tuple[str | None, str | None]:
    out: list[str] = []
    index = 1
    while index < len(value):
        if value[index] != "'":
            out.append(value[index])
            index += 1
            continue
        if index + 1 < len(value) and value[index + 1] == "'":
            out.append("'")
            index += 2
            continue
        if not _trailing_is_comment(value[index + 1 :]):
            return None, "has content after the closing quote"
        return "".join(out), None
    return None, "has an unterminated single-quoted value"


def _parse_string(value: str) -> tuple[str | None, str | None]:
    value = value.strip()
    if not value:
        return None, "must be a non-empty single-line string"

    if value.startswith('"'):
        try:
            parsed, end = json.JSONDecoder().raw_decode(value)
        except json.JSONDecodeError:
            return None, "has an invalid double-quoted value"
        if not isinstance(parsed, str):
            return None, "must be a string"
        if not _trailing_is_comment(value[end:]):
            return None, "has content after the closing quote"
        result = parsed
    elif value.startswith("'"):
        result, error = _parse_single_quoted(value)
        if error:
            return None, error
    else:
        comment = _comment_start(value)
        result = value[:comment].rstrip() if comment is not None else value
        if not result:
            return None, "must be a non-empty single-line string"
        if result[0] in "[{|>" or result.lower() in _NON_STRING_PLAIN_SCALARS:
            return None, "must be a plain or quoted single-line string"

    if result is None or not result.strip():
        return None, "must be a non-empty single-line string"
    return result, None


def _parse_order(value: str) -> tuple[int | None, str | None]:
    value = value.strip()
    comment = _comment_start(value)
    if comment is not None:
        value = value[:comment].rstrip()
    if not _INTEGER_RE.fullmatch(value):
        return None, "must be an unquoted base-10 integer"
    return int(value, 10), None


def parse_series_metadata(
    front_matter: str,
) -> tuple[SeriesMetadata | None, tuple[SeriesMetadataError, ...]]:
    """Parse the optional flat series fields from a raw front-matter block.

    No fields means the post is not in a series.  If any field is present, all
    three must be valid; errors are aggregated so one authoring pass can fix the
    entire set.
    """
    raw_values: dict[str, str] = {}
    errors: list[SeriesMetadataError] = []

    for line in front_matter.splitlines():
        match = _FIELD_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in raw_values:
            errors.append(SeriesMetadataError(key, "must not be declared more than once"))
            continue
        raw_values[key] = match.group(2) or ""

    if not raw_values:
        return None, ()

    missing = [key for key in SERIES_KEYS if key not in raw_values]
    if missing:
        errors.append(
            SeriesMetadataError(
                "series metadata",
                "is incomplete; missing " + ", ".join(missing),
            )
        )

    series_id: str | None = None
    if "series-id" in raw_values:
        series_id, error = _parse_string(raw_values["series-id"])
        if error:
            errors.append(SeriesMetadataError("series-id", error))
        elif not _SERIES_ID_RE.fullmatch(series_id or ""):
            errors.append(
                SeriesMetadataError("series-id", "must be lowercase kebab-case")
            )

    title: str | None = None
    if "series" in raw_values:
        title, error = _parse_string(raw_values["series"])
        if error:
            errors.append(SeriesMetadataError("series", error))

    order: int | None = None
    if "series-order" in raw_values:
        order, error = _parse_order(raw_values["series-order"])
        if error:
            errors.append(SeriesMetadataError("series-order", error))

    if errors:
        return None, tuple(errors)

    assert series_id is not None and title is not None and order is not None
    return SeriesMetadata(series_id, title, order), ()
