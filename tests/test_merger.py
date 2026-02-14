import pytest

from aictrl.loader import SkillData, load_skills
from aictrl.merger import deep_merge, load_overrides, merge_overrides


class TestDeepMerge:
    def test_scalar_override(self):
        base = {"name": "old", "version": "1.0"}
        override = {"version": "2.0"}
        result = deep_merge(base, override)
        assert result == {"name": "old", "version": "2.0"}

    def test_list_replaces(self):
        base = {"tags": ["a", "b"]}
        override = {"tags": ["x", "y", "z"]}
        result = deep_merge(base, override)
        assert result["tags"] == ["x", "y", "z"]

    def test_dict_deep_merges(self):
        base = {"metadata": {"a": "1", "b": "2"}}
        override = {"metadata": {"b": "3", "c": "4"}}
        result = deep_merge(base, override)
        assert result["metadata"] == {"a": "1", "b": "3", "c": "4"}

    def test_nested_dict_merge(self):
        base = {"outer": {"inner": {"a": 1, "b": 2}}}
        override = {"outer": {"inner": {"b": 3}}}
        result = deep_merge(base, override)
        assert result["outer"]["inner"] == {"a": 1, "b": 3}

    def test_delete_key(self):
        base = {"a": 1, "b": 2, "c": 3}
        override = {"_delete": ["b", "c"]}
        result = deep_merge(base, override)
        assert result == {"a": 1}

    def test_delete_nonexistent_key(self):
        base = {"a": 1}
        override = {"_delete": ["z"]}
        result = deep_merge(base, override)
        assert result == {"a": 1}

    def test_no_mutation_of_base(self):
        base = {"tags": ["a"], "metadata": {"x": "1"}}
        override = {"tags": ["b"], "metadata": {"y": "2"}}
        original_base = {"tags": ["a"], "metadata": {"x": "1"}}
        deep_merge(base, override)
        assert base == original_base

    def test_add_new_key(self):
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 2}


class TestLoadOverrides:
    def test_load_overrides(self, sample_project):
        overrides = load_overrides(sample_project)
        assert "code-review" in overrides
        assert "Edit" in overrides["code-review"]["allowed_tools"]

    def test_load_overrides_missing_dir(self, tmp_path):
        overrides = load_overrides(tmp_path)
        assert overrides == {}


class TestMergeOverrides:
    def test_merge_applies_override(self, sample_project):
        skills = load_skills(sample_project)
        merged = merge_overrides(skills, sample_project)

        cr = next(s for s in merged if s.slug == "code-review")
        assert "Edit" in cr.allowed_tools
        assert cr.metadata["team_convention"] == "always-review-tests"
        # Original metadata key preserved via deep merge
        assert cr.metadata["stack"] == "api,ui"

    def test_merge_replaces_list(self, sample_project):
        skills = load_skills(sample_project)
        merged = merge_overrides(skills, sample_project)

        cr = next(s for s in merged if s.slug == "code-review")
        # Override replaces the entire allowed_tools list
        assert cr.allowed_tools == ["Bash", "Read", "Grep", "Edit"]

    def test_merge_deep_merges_sections(self, sample_project):
        skills = load_skills(sample_project)
        merged = merge_overrides(skills, sample_project)

        cr = next(s for s in merged if s.slug == "code-review")
        # Override replaces the team_standards section
        assert "Our Team Standards" in cr.sections["team_standards"]
        # Original examples section preserved
        assert "examples" in cr.sections

    def test_unaffected_skill_unchanged(self, sample_project):
        skills = load_skills(sample_project)
        merged = merge_overrides(skills, sample_project)

        tg = next(s for s in merged if s.slug == "testing-guide")
        assert tg.allowed_tools == ["Bash", "Read", "Write"]
        assert tg.version == "2.0.1"

    def test_merge_no_overrides(self, tmp_path):
        skill = SkillData(
            slug="test", name="test", description="d", version="1.0", instructions="i"
        )
        result = merge_overrides([skill], tmp_path)
        assert len(result) == 1
        assert result[0].slug == "test"
