#!/usr/bin/env bash
set -euo pipefail

GITHUB="https://raw.githubusercontent.com/angkaberapa/github-conventional-commit-enforcer/main"
TARGET="${1:-.}"

cd "$TARGET"

echo "Downloading validator..."
curl -sL "$GITHUB/scripts/validate_commit_msg.py" -o scripts/validate_commit_msg.py
chmod +x scripts/validate_commit_msg.py

if [ ! -f .commit-enforcer.json ]; then
    echo "Creating .commit-enforcer.json..."
    cat > .commit-enforcer.json <<'JSON'
{
  "allowed_types": ["feat", "fix", "docs", "refactor", "test", "chore", "ci", "build", "perf", "revert"],
  "allowed_scopes": ["api", "auth", "db", "email", "worker", "infra"],
  "scope_required": true,
  "allow_breaking": true,
  "min_description_length": 3
}
JSON
fi

if [ ! -f .pre-commit-config.yaml ]; then
    echo "Creating .pre-commit-config.yaml..."
    cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: local
    hooks:
      - id: validate-commit-msg
        name: Validate conventional commit message
        entry: python scripts/validate_commit_msg.py
        language: system
        stages: [commit-msg]
YAML
fi

echo "Installing pre-commit hook..."
pre-commit install --hook-type commit-msg 2>/dev/null && echo "Hook installed." || echo "pre-commit not found. Install it first: pip install pre-commit"

echo ""
echo "Done. Commit messages will now be validated."
