#!/usr/bin/env python3
"""Conventional Commit message validator for pre-commit commit-msg hooks."""

import argparse
import json
import os
import re
import sys
from pathlib import Path


DEFAULT_TYPES = [
    "feat", "fix", "docs", "style", "refactor",
    "test", "chore", "ci", "build", "perf", "revert",
]

DEFAULT_CONFIG = {
    "allowed_types": DEFAULT_TYPES,
    "allowed_scopes": [],
    "scope_required": False,
    "allow_breaking": True,
    "min_description_length": 1,
}

# Search order: commitlint format first, then legacy format
CONFIG_FILENAMES = [
    ".commitlintrc.json",
    ".commitlintrc.yaml",
    ".commitlintrc.yml",
    ".commit-enforcer.json",
    ".commit-enforcer.yaml",
    ".commit-enforcer.yml",
]

# Well-known commitlint presets resolved at runtime (no npm needed)
COMMITLINT_PRESETS = {
    "@commitlint/config-conventional": {
        "type-enum": [2, "always", [
            "build", "chore", "ci", "docs", "feat",
            "fix", "perf", "refactor", "revert", "style", "test",
        ]],
    },
}

COMMIT_PATTERN = re.compile(r"^(\w+)(\([\w.\-/ ]+\))?(!)?: (.+)$", re.UNICODE)

AUTO_PREFIXES = ("merge ", "revert ", "fixup! ", "squash! ")

try:
    import yaml as _yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Config loading helpers
# ---------------------------------------------------------------------------

def _is_commitlint_config(raw: dict) -> bool:
    return "rules" in raw


def _parse_commitlint_rules(rules: dict) -> dict:
    result = {}
    if "type-enum" in rules:
        _, _, types = rules["type-enum"]
        result["allowed_types"] = types
    if "scope-enum" in rules:
        _, _, scopes = rules["scope-enum"]
        result["allowed_scopes"] = scopes
    if "scope-empty" in rules:
        _, condition, *_ = rules["scope-empty"]
        result["scope_required"] = condition == "never"
    if "subject-min-length" in rules:
        _, _, length = rules["subject-min-length"]
        result["min_description_length"] = length
    return result


def _commitlint_to_internal(raw: dict) -> dict:
    result = {}

    rules = {}
    for ext in raw.get("extends", []):
        if ext in COMMITLINT_PRESETS:
            rules.update(COMMITLINT_PRESETS[ext])

    rules.update(raw.get("rules", {}))
    result.update(_parse_commitlint_rules(rules))

    if "allow-breaking" in raw:
        result["allow_breaking"] = raw["allow-breaking"]

    return result


def _read_config_file(config_path: Path) -> dict | None:
    try:
        if config_path.suffix == ".json":
            with open(config_path) as f:
                return json.load(f)
        elif HAS_YAML:
            with open(config_path) as f:
                return _yaml.safe_load(f)
        else:
            print(
                f"Warning: found {config_path.name} but PyYAML is not available, skipping",
                file=sys.stderr,
            )
            return None
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Warning: failed to parse {config_path}: {exc}", file=sys.stderr)
        return None


def validate_config_schema(config: dict) -> None:
    errors = []

    expected = [
        ("allowed_types", list),
        ("allowed_scopes", list),
        ("scope_required", bool),
        ("allow_breaking", bool),
        ("min_description_length", int),
    ]

    for key, expected_type in expected:
        if key in config:
            val = config[key]
            if not isinstance(val, expected_type):
                errors.append(
                    f"config key '{key}' must be {expected_type.__name__}, "
                    f"got {type(val).__name__}"
                )

    for key in ("allowed_types", "allowed_scopes"):
        if key in config and isinstance(config.get(key), list):
            for i, item in enumerate(config[key]):
                if not isinstance(item, str):
                    errors.append(
                        f"config key '{key}[{i}]' must be a string, "
                        f"got {type(item).__name__}"
                    )

    desc_key = "min_description_length"
    if desc_key in config and isinstance(config.get(desc_key), int):
        if config[desc_key] < 0:
            errors.append(f"config key '{desc_key}' must be non-negative")

    if errors:
        raise ValueError("\n".join(errors))


def load_config(repo_root: Path) -> dict:
    for name in CONFIG_FILENAMES:
        config_path = repo_root / name
        if not config_path.is_file():
            continue

        raw = _read_config_file(config_path)
        if raw is None or not isinstance(raw, dict):
            continue

        config = dict(DEFAULT_CONFIG)
        if _is_commitlint_config(raw):
            config.update(_commitlint_to_internal(raw))
        else:
            config.update(raw)

        try:
            validate_config_schema(config)
        except ValueError as exc:
            print(f"Error: invalid config in {name}\n{exc}", file=sys.stderr)
            sys.exit(1)
        return config

    return dict(DEFAULT_CONFIG)


def is_auto_commit(first_line: str) -> bool:
    lower = first_line.strip().lower()
    for prefix in AUTO_PREFIXES:
        if lower.startswith(prefix):
            return True
    return False


def validate(message: str, config: dict) -> str | None:
    first_line = message.strip().split("\n")[0]

    if not first_line:
        return "commit message is empty"

    if is_auto_commit(first_line):
        return None

    match = COMMIT_PATTERN.match(first_line)
    if not match:
        return (
            f"format mismatch\n"
            f"  expected: <type>(optional-scope): <description>\n"
            f"  got:      {first_line}"
        )

    commit_type = match.group(1)
    scope_raw = match.group(2)
    bang = match.group(3)
    description = match.group(4)

    allowed_types = config.get("allowed_types", DEFAULT_TYPES)
    if commit_type not in allowed_types:
        return f"type '{commit_type}' is not allowed"

    scope_str = scope_raw[1:-1] if scope_raw else None

    if config.get("scope_required", False) and not scope_str:
        return "scope is required but missing"

    allowed_scopes = config.get("allowed_scopes", [])
    if allowed_scopes and scope_str and scope_str not in allowed_scopes:
        return f"scope '{scope_str}' is not allowed"

    if bang and not config.get("allow_breaking", True):
        return "breaking change marker '!' is not allowed"

    min_desc = config.get("min_description_length", 1)
    if len(description) < min_desc:
        return f"description is too short ({len(description)} < {min_desc})"

    return None


def format_error(detail: str, config: dict) -> str:
    lines = [
        "INVALID COMMIT MESSAGE",
        "",
        "Error: " + detail,
        "",
        "Expected format:",
        "  <type>(optional-scope)<!:> <description>",
        "",
        "Valid examples:",
        "  feat(auth): add login token refresh",
        "  fix(api): handle missing user email",
        "  docs: update setup guide",
        "  feat(api)!: remove legacy endpoint",
        "  feat!: change public API",
        "",
        "Allowed types: " + ", ".join(config.get("allowed_types", DEFAULT_TYPES)),
    ]

    scopes = config.get("allowed_scopes", [])
    if scopes:
        lines.append("Allowed scopes: " + ", ".join(scopes))

    if config.get("scope_required", False):
        lines.append("Scope is REQUIRED.")
    else:
        lines.append("Scope is optional.")

    if config.get("allow_breaking", True):
        lines.append("Breaking changes (marker '!') are allowed.")
    else:
        lines.append("Breaking changes (marker '!') are NOT allowed.")

    lines.append("")
    lines.append("To skip checks: git commit --no-verify")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate conventional commit messages."
    )
    parser.add_argument(
        "commit_msg_file",
        nargs="?",
        help="Path to the commit message file",
    )
    parser.add_argument(
        "--pr-mode",
        type=str,
        default=None,
        help="Validate a PR title/description string instead of reading a file",
    )
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Path to config file (default: look for .commitlintrc.json "
            "or .commit-enforcer.json in repo root)"
        ),
    )
    args = parser.parse_args()

    if bool(args.pr_mode) == bool(args.commit_msg_file):
        parser.error("provide either --pr-mode <string> or a commit_msg_file, not both")

    if args.config:
        config_path = Path(args.config)
        if config_path.is_file():
            raw = _read_config_file(config_path)
            if raw is None or not isinstance(raw, dict):
                raw = {}
            config = dict(DEFAULT_CONFIG)
            if _is_commitlint_config(raw):
                config.update(_commitlint_to_internal(raw))
            else:
                config.update(raw)
            try:
                validate_config_schema(config)
            except ValueError as exc:
                print(f"Error: invalid config\n{exc}", file=sys.stderr)
                return 1
        else:
            print(
                f"Warning: config file '{args.config}' not found, using defaults",
                file=sys.stderr,
            )
            config = dict(DEFAULT_CONFIG)
    else:
        repo_root = Path(os.getcwd())
        config = load_config(repo_root)

    if args.pr_mode:
        message = args.pr_mode
    else:
        try:
            with open(args.commit_msg_file) as f:
                message = f.read()
        except OSError as exc:
            print(f"Error reading commit message file: {exc}", file=sys.stderr)
            return 1

    error = validate(message, config)
    if error:
        print(format_error(error, config))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
