#!/usr/bin/env bash
set -euo pipefail

GITHUB="https://raw.githubusercontent.com/angkaberapa/github-conventional-commit-enforcer/main"
TARGET="${1:-.}"
PY="${PYTHON:-python3}"

cd "$TARGET"

mkdir -p scripts
echo "Downloading validator..."
curl -sL "$GITHUB/scripts/validate_commit_msg.py" -o scripts/validate_commit_msg.py
chmod +x scripts/validate_commit_msg.py
echo "  -> scripts/validate_commit_msg.py"

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
    cat > .pre-commit-config.yaml <<YAML
repos:
  - repo: local
    hooks:
      - id: validate-commit-msg
        name: Validate conventional commit message
        entry: $PY scripts/validate_commit_msg.py
        language: system
        stages: [commit-msg]
YAML
elif ! grep -q "validate-commit-msg" .pre-commit-config.yaml 2>/dev/null; then
    echo "Warning: .pre-commit-config.yaml exists but does not include our hook."
    echo "Add the following to your .pre-commit-config.yaml under 'repos:':"
    echo ""
    echo "  - repo: local"
    echo "    hooks:"
    echo "      - id: validate-commit-msg"
    echo "        name: Validate conventional commit message"
    echo "        entry: $PY scripts/validate_commit_msg.py"
    echo "        language: system"
    echo "        stages: [commit-msg]"
    echo ""
fi

echo "Installing pre-commit hook..."
if command -v pre-commit &>/dev/null; then
    pre-commit install --hook-type commit-msg 2>&1 && echo "Hook installed." || echo "Warning: pre-commit install failed (not a git repository?)."
else
    echo "pre-commit not found. Install it first: pip install pre-commit"
fi

echo ""
echo "Verifying validator..."
if "$PY" scripts/validate_commit_msg.py --pr-mode "feat(api): test" >/dev/null 2>&1; then
    echo "✓ Validator is working correctly."
else
    echo "✗ Validator check failed. Something went wrong."
fi

echo ""
echo "Done. Commit messages will now be validated."
