# commit-enforcer

A zero-dependency Conventional Commit message enforcer for `pre-commit` hooks and CI.

## Features

- Validates commit messages against the [Conventional Commits] spec
- Configurable types, scopes, breaking changes, description length
- Auto-commits (merge, revert, fixup!, squash!) pass automatically
- Works as a pre-commit hook, standalone CLI, or CI validation
- Zero runtime dependencies (PyYAML optional for YAML config)

## Quick start

### Prerequisite

```bash
pip install pre-commit
```

### Setup in one command

```bash
curl -sSL https://raw.githubusercontent.com/angkaberapa/github-conventional-commit-enforcer/main/scripts/install.sh | bash
```

This downloads the validator, creates config files, and installs the hook. Done.

### Alternative: manual setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-commit-msg
        name: Validate conventional commit message
        entry: python scripts/validate_commit_msg.py
        language: system
        stages: [commit-msg]
```

```bash
pre-commit install --hook-type commit-msg
```

### Install from GitHub (for local development)

```bash
pip install git+https://github.com/angkaberapa/github-conventional-commit-enforcer
```

## CLI usage

```bash
validate-commit-msg .git/COMMIT_EDITMSG         # validate from file
validate-commit-msg --pr-mode "feat(api): add health check"   # validate string
validate-commit-msg --config /path/to/config.json .git/COMMIT_EDITMSG  # explicit config
```

## CI/CD

```yaml
- name: Validate PR title
  run: validate-commit-msg --pr-mode "${{ github.event.pull_request.title }}"
```

## Configuration

Create `.commit-enforcer.json` (or `.yaml`/`.yml`) in the repository root:

```json
{
  "allowed_types": ["feat", "fix", "docs", "refactor", "test", "chore", "ci", "build", "perf", "revert"],
  "allowed_scopes": ["api", "auth", "db"],
  "scope_required": true,
  "allow_breaking": true,
  "min_description_length": 3
}
```

| Key | Type | Default | Description |
|---|---|---|---|
| `allowed_types` | `list[str]` | *(see below)* | Allowed commit types |
| `allowed_scopes` | `list[str]` | `[]` | Allowed scopes (empty = any) |
| `scope_required` | `bool` | `false` | Scope is mandatory |
| `allow_breaking` | `bool` | `true` | Allow `!` marker |
| `min_description_length` | `int` | `1` | Min description length |

Default types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, `revert`

## Development

```bash
pip install -e .
pip install PyYAML    # optional: YAML config support
pytest tests/         # unit tests
bash scripts/test_integration.sh  # integration tests
```

## Bypass

```bash
git commit --no-verify -m "bypass validation"
```

[Conventional Commits]: https://www.conventionalcommits.org/
