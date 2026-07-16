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

## Setup for contributors

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

## Setup in a new repository

In the target repository, run:

```bash
curl -sSL https://raw.githubusercontent.com/angkaberapa/github-conventional-commit-enforcer/main/scripts/install.sh | bash
```

This downloads `validate_commit_msg.py`, creates `.commit-enforcer.json` and `.pre-commit-config.yaml`, and installs the hook.

**Prerequisite:** Python 3 + `pre-commit` (`pip install pre-commit`).

## Per-repository customization

To customize behavior, create a `.commit-enforcer.json` (or `.commit-enforcer.yaml`) file in the repository root.

The script reads this file and adapts its rules automatically — no code changes needed.

```json
{
  "allowed_types": ["feat", "fix", "docs", "chore"],
  "allowed_scopes": ["api", "auth", "db"],
  "scope_required": true,
  "allow_breaking": true
}
```

Available configuration keys:

| Key | Type | Default | Description |
|---|---|---|---|
| `allowed_types` | `list[str]` | default types (see above) | Allowed commit types |
| `allowed_scopes` | `list[str]` | `[]` | Allowed scopes (empty = any scope allowed) |
| `scope_required` | `bool` | `false` | Whether scope is mandatory |
| `allow_breaking` | `bool` | `true` | Whether `!` marker is allowed |
| `min_description_length` | `int` | `1` | Minimum description length |

### Config validation

If a config value has the wrong type (e.g. `"allowed_types": "feat"` instead of a list), the script prints a clear error and exits. Example:

```
Error: invalid config in .commit-enforcer.json
config key 'allowed_types' must be list, got str
```

## CI/CD usage

The validator can be reused in CI/CD pipelines via the `--pr-mode` flag:

```bash
validate-commit-msg --pr-mode "feat(api): add health check"
```

This validates a string directly without reading a commit message file, making it suitable for pull request title validation.

Example GitHub Actions step:

```yaml
- name: Validate PR title
  run: validate-commit-msg --pr-mode "${{ github.event.pull_request.title }}"
```

## Running tests

Unit tests:

```bash
pip install -e .
pytest tests/
```

Integration tests:

```bash
bash scripts/test_integration.sh
```
