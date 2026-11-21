"""Shared helpers: canonical JSON, digests, typed errors."""

import hashlib
import json


class CaseError:
    """One validation finding, anchored to a JSON field path."""

    def __init__(self, path, message):
        self.path = path
        self.message = message

    def to_json(self):
        return {"path": self.path, "message": self.message}

    def __repr__(self):
        return f"CaseError({self.path!r}, {self.message!r})"


class FormatErrors(Exception):
    """Raised when an input document is malformed."""

    def __init__(self, errors):
        super().__init__("; ".join(f"{e.path}: {e.message}" for e in errors))
        self.errors = list(errors)


class SearchOverflow(Exception):
    """Raised when an enumeration exceeds its deterministic safety cap."""


def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise FormatErrors([CaseError("$", f"cannot read file: {exc}")])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise FormatErrors([CaseError("$", f"invalid JSON: {exc}")])


def canonical_json(obj):
    """Reproducible UTF-8 JSON: sorted keys, fixed indent, trailing newline."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def compact_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def input_digest(obj):
    return hashlib.sha256(compact_json(obj).encode("utf-8")).hexdigest()


def first_diff(expected, actual, path="$"):
    """Return the JSON path of the first difference (deterministic order)."""
    if type(expected) is not type(actual):
        return path
    if isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                return f"{path}.{key}"
            sub = first_diff(expected[key], actual[key], f"{path}.{key}")
            if sub:
                return sub
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}.length"
        for i, (exp, act) in enumerate(zip(expected, actual)):
            sub = first_diff(exp, act, f"{path}[{i}]")
            if sub:
                return sub
        return None
    return None if expected == actual else path
