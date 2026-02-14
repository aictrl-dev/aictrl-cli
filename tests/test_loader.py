from aictrl.loader import load_skills, load_skill, SkillData


def test_load_skills_returns_all_skills(sample_project):
    skills = load_skills(sample_project)
    assert len(skills) == 2
    slugs = [s.slug for s in skills]
    assert "code-review" in slugs
    assert "testing-guide" in slugs


def test_load_skills_returns_skill_data(sample_project):
    skills = load_skills(sample_project)
    cr = next(s for s in skills if s.slug == "code-review")

    assert cr.name == "code-review"
    assert cr.version == "1.2.3"
    assert "code review assistant" in cr.instructions.lower()
    assert cr.description == "Guides thorough code reviews with security and performance focus"
    assert cr.tags == ["review", "quality", "security"]
    assert cr.allowed_tools == ["Bash", "Read", "Grep"]
    assert cr.metadata == {"stack": "api,ui"}


def test_load_skills_sections(sample_project):
    skills = load_skills(sample_project)
    cr = next(s for s in skills if s.slug == "code-review")

    assert "examples" in cr.sections
    assert "team_standards" in cr.sections
    assert "SQL injection" in cr.sections["examples"]


def test_load_skills_empty_dir(tmp_path):
    skills_dir = tmp_path / ".aictrl" / "data" / "skills"
    skills_dir.mkdir(parents=True)
    skills = load_skills(tmp_path)
    assert skills == []


def test_load_skills_missing_dir(tmp_path):
    skills = load_skills(tmp_path)
    assert skills == []


def test_load_skill_single_file(sample_project):
    yaml_path = sample_project / ".aictrl" / "data" / "skills" / "testing-guide.yaml"
    skill = load_skill(yaml_path)
    assert skill.slug == "testing-guide"
    assert skill.version == "2.0.1"
    assert "Vitest" in skill.instructions


def test_load_skills_sorted(sample_project):
    skills = load_skills(sample_project)
    slugs = [s.slug for s in skills]
    assert slugs == sorted(slugs)
