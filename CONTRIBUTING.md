# Contributing

## Commit message convention

This repository enforces **Conventional Commits** for all commit messages.

### Format

```
<type>(optional-scope)<!:> <description>
```

### Valid examples

```
feat(auth): add login token refresh
fix(api): handle missing user email
docs: update setup guide
chore: update dependencies
feat(api)!: remove legacy endpoint
feat!: change public API
```

### Invalid examples

```
update stuff
fix bug
WIP
added login
```

### Allowed types

- `feat` — a new feature
- `fix` — a bug fix
- `docs` — documentation only changes
- `style` — formatting, missing semicolons, etc. (no code change)
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or updating tests
- `chore` — maintenance, tooling, dependencies
- `ci` — CI/CD configuration changes
- `build` — build system or external dependency changes
- `perf` — performance improvement
- `revert` — reverting a previous commit

## Setup

### 1. Install pre-commit

Recommended:

```bash
pipx install pre-commit
```

Fallback:

```bash
pip install pre-commit
```

### 2. Install the hook

From the repository root:

```bash
pre-commit install --hook-type commit-msg
```

The hook will run automatically during `git commit` and validate your commit message.

### 3. Fix a rejected commit

If the hook blocks your commit, edit your message and retry:

```bash
git commit --edit
```

Or use `--no-verify` to bypass the hook (intended for emergencies only):

```bash
git commit --no-verify -m "your message"
```

## Per-repository customization

To customize allowed types, scopes, or other rules, create a `.commit-msg.json` file in the repository root:

```json
{
  "types": ["feat", "fix", "docs", "chore"],
  "scopes": ["api", "auth", "ui"],
  "scope_required": true,
  "breaking_allowed": true
}
```

Available configuration keys:

| Key | Type | Default | Description |
|---|---|---|---|
| `types` | `list[str]` | default types (see above) | Allowed commit types |
| `scopes` | `list[str]` | `[]` | Allowed scopes (empty = any scope allowed) |
| `scope_required` | `bool` | `false` | Whether scope is mandatory |
| `breaking_allowed` | `bool` | `true` | Whether `!` marker is allowed |
| `min_description_length` | `int` | `1` | Minimum description length |
