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

CONFIG_FILENAME = ".commit-enforcer.json"

COMMIT_PATTERN = re.compile(r"^(\w+)(\([\w.\-/ ]+\))?(!)?: (.+)$", re.UNICODE)

AUTO_PREFIXES = ("merge ", "revert ", "fixup! ", "squash! ")


def load_config(repo_root: Path) -> dict:
    config_path = repo_root / CONFIG_FILENAME
    if config_path.is_file():
        with open(config_path) as f:
            user_config = json.load(f)
        config = dict(DEFAULT_CONFIG)
        config.update(user_config)
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
    parser.add_argument("commit_msg_file", help="Path to the commit message file")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config file (default: look for .commit-enforcer.json in repo root)",
    )
    args = parser.parse_args()

    commit_msg_file = Path(args.commit_msg_file)

    if args.config:
        config_path = Path(args.config)
        if config_path.is_file():
            with open(config_path) as f:
                config = dict(DEFAULT_CONFIG)
                config.update(json.load(f))
        else:
            print(f"Warning: config file '{args.config}' not found, using defaults",
                  file=sys.stderr)
            config = dict(DEFAULT_CONFIG)
    else:
        repo_root = Path(os.getcwd())
        config = load_config(repo_root)

    try:
        with open(commit_msg_file) as f:
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
