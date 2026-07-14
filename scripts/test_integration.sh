#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PASS=0
FAIL=0
TMP_CONFIG=".commit-enforcer.json"

cleanup() {
    git reset --soft HEAD~"$1" 2>/dev/null || true
}

ok()   { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Integration test suite ==="
echo ""

# --- default config ---
echo "--- With repo .commit-enforcer.json ---"

if git commit --allow-empty -m "feat(api): valid commit" 2>/dev/null; then
    ok "valid commit passes"
else
    fail "valid commit should pass"
fi

if ! git commit --allow-empty -m "bad message" 2>/dev/null; then
    ok "invalid format blocked"
else
    fail "invalid format should block"
fi

cleanup 1

# --- custom config ---
echo ""
echo "--- Override with custom .commit-enforcer.json ---"

cat > "$TMP_CONFIG" <<'EOF'
{
  "allowed_types": ["feat", "fix"],
  "allowed_scopes": ["api", "auth"],
  "scope_required": true,
  "allow_breaking": false,
  "min_description_length": 3
}
EOF

git add "$TMP_CONFIG"

if git commit --allow-empty -m "feat(api): valid custom" 2>/dev/null; then
    ok "valid custom commit passes"
else
    fail "valid custom commit should pass"
fi

if ! git commit --allow-empty -m "docs: not allowed" 2>/dev/null; then
    ok "invalid type blocked"
else
    fail "invalid type should block"
fi

if ! git commit --allow-empty -m "feat(ui): bad scope" 2>/dev/null; then
    ok "invalid scope blocked"
else
    fail "invalid scope should block"
fi

if ! git commit --allow-empty -m "feat: missing scope" 2>/dev/null; then
    ok "missing scope blocked"
else
    fail "missing scope should block"
fi

if ! git commit --allow-empty -m "feat(api)!: breaking" 2>/dev/null; then
    ok "breaking marker blocked"
else
    fail "breaking marker should block"
fi

if ! git commit --allow-empty -m "feat(api): ab" 2>/dev/null; then
    ok "short description blocked"
else
    fail "short description should block"
fi

cleanup 1
git rm --cached "$TMP_CONFIG" 2>/dev/null || true
rm -f "$TMP_CONFIG"

# --- auto-generated commits ---
echo ""
echo "--- Auto-generated commits ---"

if git commit --allow-empty -m "Merge branch feature" 2>/dev/null; then
    ok "merge commit passes"
else
    fail "merge commit should pass"
fi

if git commit --allow-empty -m "fixup! feat(api): squash" 2>/dev/null; then
    ok "fixup! commit passes"
else
    fail "fixup! commit should pass"
fi

cleanup 2

# --- YAML config ---
echo ""
echo "--- YAML config ---"

cat > ".commit-enforcer.yaml" <<'EOF'
allowed_types:
  - feat
  - fix
allowed_scopes:
  - api
scope_required: true
allow_breaking: true
min_description_length: 2
EOF

git add ".commit-enforcer.yaml"

if git commit --allow-empty -m "feat(api): yaml config works" 2>/dev/null; then
    ok "YAML config loads correctly"
else
    fail "YAML config should load"
fi

cleanup 1
git rm --cached ".commit-enforcer.yaml" 2>/dev/null || true
rm -f ".commit-enforcer.yaml"

# --- summary ---
echo ""
echo "=============================="
echo "Results: $PASS passed, $FAIL failed"
echo "=============================="

exit $FAIL
