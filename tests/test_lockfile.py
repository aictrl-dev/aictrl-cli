from aictrl.loader import SkillData, load_skills
from aictrl.lockfile import (
    compute_skill_hash,
    read_lockfile,
    write_lockfile,
    is_stale,
)


def _make_skill(slug="test", version="1.0", instructions="do things"):
    return SkillData(
        slug=slug, name=slug, description=f"Test {slug}",
        version=version, instructions=instructions,
    )


class TestComputeHash:
    def test_deterministic(self):
        s1 = _make_skill()
        s2 = _make_skill()
        assert compute_skill_hash(s1) == compute_skill_hash(s2)

    def test_changes_with_version(self):
        s1 = _make_skill(version="1.0")
        s2 = _make_skill(version="2.0")
        assert compute_skill_hash(s1) != compute_skill_hash(s2)

    def test_changes_with_instructions(self):
        s1 = _make_skill(instructions="a")
        s2 = _make_skill(instructions="b")
        assert compute_skill_hash(s1) != compute_skill_hash(s2)


class TestReadWriteLockfile:
    def test_write_and_read(self, tmp_path):
        skills = [_make_skill("alpha", "1.0"), _make_skill("beta", "2.0")]

        # Create .aictrl directory structure
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()

        write_lockfile(tmp_path, skills)
        lock = read_lockfile(tmp_path)

        assert lock is not None
        assert lock.version == 1
        assert len(lock.skills) == 2
        assert lock.skills[0].slug == "alpha"
        assert lock.skills[1].slug == "beta"

    def test_read_missing(self, tmp_path):
        lock = read_lockfile(tmp_path)
        assert lock is None

    def test_entries_sorted_by_slug(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("zebra"), _make_skill("alpha")]
        write_lockfile(tmp_path, skills)
        lock = read_lockfile(tmp_path)
        assert lock.skills[0].slug == "alpha"
        assert lock.skills[1].slug == "zebra"


class TestIsStale:
    def test_no_lockfile_is_stale(self, tmp_path):
        skills = [_make_skill()]
        assert is_stale(tmp_path, skills) is True

    def test_fresh_after_write(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("a"), _make_skill("b")]
        write_lockfile(tmp_path, skills)
        assert is_stale(tmp_path, skills) is False

    def test_stale_after_version_change(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("a", "1.0")]
        write_lockfile(tmp_path, skills)

        updated = [_make_skill("a", "2.0")]
        assert is_stale(tmp_path, updated) is True

    def test_stale_after_content_change(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("a", instructions="old")]
        write_lockfile(tmp_path, skills)

        updated = [_make_skill("a", instructions="new")]
        assert is_stale(tmp_path, updated) is True

    def test_stale_after_skill_added(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("a")]
        write_lockfile(tmp_path, skills)

        updated = [_make_skill("a"), _make_skill("b")]
        assert is_stale(tmp_path, updated) is True

    def test_stale_after_skill_removed(self, tmp_path):
        aictrl_dir = tmp_path / ".aictrl"
        aictrl_dir.mkdir()
        skills = [_make_skill("a"), _make_skill("b")]
        write_lockfile(tmp_path, skills)

        updated = [_make_skill("a")]
        assert is_stale(tmp_path, updated) is True

    def test_with_fixture_data(self, sample_project, tmp_path):
        import shutil
        # Copy the fixture to a writable location
        dst = tmp_path / "project"
        shutil.copytree(sample_project, dst)

        skills = load_skills(dst)
        # No lockfile with correct hashes, so should be stale
        assert is_stale(dst, skills) is True

        write_lockfile(dst, skills)
        assert is_stale(dst, skills) is False
