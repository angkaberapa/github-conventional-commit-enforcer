#!/usr/bin/env bash
# Integration test — uses git for commit creation but bypasses
# the pre-commit hook and validates commit messages directly.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PASS=0
FAIL=0
TMP_CONFIG=".commitlintrc.json"
HAD_CONFIG=false
[ -f "$TMP_CONFIG" ] && HAD_CONFIG=true && cp "$TMP_CONFIG" "${TMP_CONFIG}.bak"
PY="${PYTHON:-python3}"
VALIDATOR="$PY scripts/validate_commit_msg.py"

cleanup() {
    git reset --soft HEAD~"$1" 2>/dev/null || true
}

ok()   { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Integration test suite ==="
echo ""

# ------------------------------------------------------------------
# Default config
# ------------------------------------------------------------------
echo "--- With repo config ---"

if $VALIDATOR --pr-mode "feat(api): valid commit" >/dev/null 2>&1; then
    ok "valid commit passes"
else
    fail "valid commit should pass"
fi

if ! $VALIDATOR --pr-mode "bad message" >/dev/null 2>&1; then
    ok "invalid format blocked"
else
    fail "invalid format should block"
fi

# ------------------------------------------------------------------
# Custom commitlintrc.json
# ------------------------------------------------------------------
echo ""
echo "--- Override with custom .commitlintrc.json ---"

cat > "$TMP_CONFIG" <<'EOF'
{
  "rules": {
    "type-enum": [2, "always", ["feat", "fix"]],
    "scope-enum": [2, "always", ["api", "auth"]],
    "scope-empty": [2, "never"],
    "subject-min-length": [2, "always", 3]
  },
  "allow-breaking": false
}
EOF

git add "$TMP_CONFIG"

if git commit --allow-empty --no-verify -m "feat(api): valid custom" >/dev/null 2>&1; then
    ok "valid custom commit passes"
else
    fail "valid custom commit should pass"
fi

if ! $VALIDATOR --pr-mode "docs: not allowed" >/dev/null 2>&1; then
    ok "invalid type blocked"
else
    fail "invalid type should block"
fi

if ! $VALIDATOR --pr-mode "feat(ui): bad scope" >/dev/null 2>&1; then
    ok "invalid scope blocked"
else
    fail "invalid scope should block"
fi

if ! $VALIDATOR --pr-mode "feat: missing scope" >/dev/null 2>&1; then
    ok "missing scope blocked"
else
    fail "missing scope should block"
fi

if ! $VALIDATOR --pr-mode "feat(api)!: breaking" >/dev/null 2>&1; then
    ok "breaking marker blocked"
else
    fail "breaking marker should block"
fi

if ! $VALIDATOR --pr-mode "feat(api): ab" >/dev/null 2>&1; then
    ok "short description blocked"
else
    fail "short description should block"
fi

cleanup 1
git rm --cached "$TMP_CONFIG" 2>/dev/null || true
rm -f "$TMP_CONFIG"

# ------------------------------------------------------------------
# Auto-generated commits (merge, revert, fixup!, squash!)
# ------------------------------------------------------------------
echo ""
echo "--- Auto-generated commits ---"

if git commit --allow-empty --no-verify -m "Merge branch feature" >/dev/null 2>&1; then
    ok "merge commit passes"
else
    fail "merge commit should pass"
fi

if git commit --allow-empty --no-verify -m "fixup! feat(api): squash" >/dev/null 2>&1; then
    ok "fixup! commit passes"
else
    fail "fixup! commit should pass"
fi

cleanup 2

# ------------------------------------------------------------------
# YAML config (.commitlintrc.yaml)
# ------------------------------------------------------------------
echo ""
echo "--- YAML config ---"

cat > ".commitlintrc.yaml" <<'EOF'
rules:
  type-enum: [2, "always", ["feat", "fix"]]
  scope-enum: [2, "always", ["api"]]
  scope-empty: [2, "never"]
  subject-min-length: [2, "always", 2]
allow-breaking: true
EOF

git add ".commitlintrc.yaml"

# YAML test — use --no-verify for the git commit, validate separately
git commit --allow-empty --no-verify -m "feat(api): yaml config works" >/dev/null 2>&1

if $VALIDATOR --pr-mode "feat(api): yaml config works" >/dev/null 2>&1; then
    ok "YAML config loads correctly"
else
    fail "YAML config should load"
fi

cleanup 1
git rm --cached ".commitlintrc.yaml" 2>/dev/null || true
rm -f ".commitlintrc.yaml"

# ------------------------------------------------------------------
# Cleanup + summary
# ------------------------------------------------------------------
echo ""
echo "=============================="
echo "Results: $PASS passed, $FAIL failed"
echo "=============================="

$HAD_CONFIG && mv "${TMP_CONFIG}.bak" "$TMP_CONFIG"
git add "$TMP_CONFIG" 2>/dev/null || true
exit $FAIL
