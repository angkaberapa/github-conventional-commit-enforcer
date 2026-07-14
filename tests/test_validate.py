import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_commit_msg import validate, DEFAULT_TYPES, DEFAULT_CONFIG


def mkconfig(**overrides):
    c = dict(DEFAULT_CONFIG)
    c.update(overrides)
    return c


class TestAutoCommit:
    def test_merge(self):
        assert validate("Merge branch 'feature'\n", {}) is None

    def test_revert(self):
        assert validate("Revert 'feat: add thing'\n", {}) is None

    def test_fixup(self):
        assert validate("fixup! feat(api): add health check\n", {}) is None

    def test_squash(self):
        assert validate("squash! feat(api): add health check\n", {}) is None

    def test_merge_case_insensitive(self):
        assert validate("MERGE branch\n", {}) is None

    def test_fixup_no_space_bang_not_auto(self):
        err = validate("fixup: not a fixup commit\n", {})
        assert err is not None


class TestEmpty:
    def test_empty_string(self):
        assert validate("", {}) is not None

    def test_only_whitespace(self):
        assert validate("  \n", {}) is not None


class TestFormat:
    def test_valid_format_no_scope(self):
        assert validate("feat: add feature\n", {}) is None

    def test_valid_format_with_scope(self):
        assert validate("feat(api): add endpoint\n", {}) is None

    def test_valid_format_breaking_no_scope(self):
        assert validate("feat!: breaking change\n", {}) is None

    def test_valid_format_breaking_with_scope(self):
        assert validate("feat(api)!: breaking\n", {}) is None

    def test_missing_colon_space(self):
        assert validate("feat:add feature\n", {}) is not None

    def test_missing_space_after_colon(self):
        assert validate("feat:add feature\n", {}) is not None

    def test_no_type_prefix(self):
        assert validate(": add feature\n", {}) is not None

    def test_subject_only_no_description(self):
        assert validate("feat:", {}) is not None


class TestType:
    def test_default_types_pass(self):
        for t in DEFAULT_TYPES:
            assert validate(f"{t}: ok\n", {}) is None, f"type {t} should pass"

    def test_invalid_type_blocked(self):
        config = mkconfig(allowed_types=["feat", "fix"])
        assert validate("docs: not allowed\n", config) is not None

    def test_case_sensitive(self):
        assert validate("Feat: case sensitive\n", {}) is not None


class TestScope:
    def test_scope_optional_passes(self):
        config = mkconfig(scope_required=False)
        assert validate("feat: no scope\n", config) is None

    def test_scope_required_missing_blocked(self):
        config = mkconfig(scope_required=True)
        assert validate("feat: missing scope\n", config) is not None

    def test_scope_required_present_passes(self):
        config = mkconfig(scope_required=True, allowed_scopes=["api"])
        assert validate("feat(api): has scope\n", config) is None

    def test_invalid_scope_blocked(self):
        config = mkconfig(allowed_scopes=["api", "auth"])
        assert validate("feat(ui): bad scope\n", config) is not None

    def test_empty_scopes_list_means_any(self):
        config = mkconfig(allowed_scopes=[])
        assert validate("feat(whatever): any scope\n", config) is None

    def test_dotted_scope(self):
        assert validate("feat(api/v2): dotted scope\n", {}) is None

    def test_hyphenated_scope(self):
        assert validate("feat(my-scope): hyphenated\n", {}) is None


class TestBreaking:
    def test_breaking_allowed_passes(self):
        config = mkconfig(allow_breaking=True)
        assert validate("feat!: breaking\n", config) is None

    def test_breaking_blocked(self):
        config = mkconfig(allow_breaking=False)
        assert validate("feat!: breaking\n", config) is not None

    def test_breaking_blocked_with_scope(self):
        config = mkconfig(allow_breaking=False)
        assert validate("feat(api)!: breaking\n", config) is not None

    def test_non_breaking_passes_when_breaking_blocked(self):
        config = mkconfig(allow_breaking=False)
        assert validate("feat: normal\n", config) is None


class TestDescriptionLength:
    def test_short_description_blocked(self):
        config = mkconfig(min_description_length=10)
        assert validate("feat: short\n", config) is not None

    def test_long_enough_description_passes(self):
        config = mkconfig(min_description_length=10)
        assert validate("feat: long enough description\n", config) is None

    def test_default_min_length_allows_one_char(self):
        assert validate("feat: x\n", {}) is None


class TestMultiLine:
    def test_body_ignored(self):
        msg = "feat(api): subject line\n\nBody content here.\n"
        assert validate(msg, {}) is None

    def test_subject_only(self):
        msg = "fix(scope): subject"
        assert validate(msg, {}) is None
