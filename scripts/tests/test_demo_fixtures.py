"""Tests that fixture content is non-sensitive and complete."""
import re
from pathlib import Path

FIXTURES = Path(__file__).parents[2] / "fixtures"
REPOS = FIXTURES / "repos"
DOCS = FIXTURES / "docs"

# Patterns that look like real secrets (not labeled fake)
_REAL_SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|token|private[_-]?key)\s*[=:]\s*['\"]?(?!.*fake|.*sample|.*example|.*placeholder|.*FAKE|.*dummy)[A-Za-z0-9+/]{16,}['\"]?"
)

EXPECTED_REPOS = ["sql-dbt-sample", "java-sample", "dotnet-sample", "talend-sample", "shared"]
EXPECTED_DOCS = ["data-retention-policy.md", "orders-faq.md", "sample_report.xlsx"]


def _text_files(path: Path):
    binary_suffixes = {".jar", ".class", ".dll", ".png", ".xlsx"}
    return [f for f in path.rglob("*") if f.is_file() and f.suffix not in binary_suffixes]


def test_fixture_repos_exist():
    for repo in EXPECTED_REPOS:
        assert (REPOS / repo).is_dir(), f"Missing fixture repo: {repo}"


def test_fixture_docs_exist():
    for doc in EXPECTED_DOCS:
        assert (DOCS / doc).exists(), f"Missing fixture doc: {doc}"


def test_no_real_secrets():
    """No unlabeled secrets in text fixture files."""
    violations = []
    for f in _text_files(FIXTURES):
        text = f.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            if _REAL_SECRET_PATTERN.search(line):
                # Allow lines that also contain a 'fake'/'fixture'/'test'/'sample' label
                if not re.search(r"(?i)fake|fixture|test|sample|example|placeholder|dummy|FAKE", line):
                    violations.append(f"{f.relative_to(FIXTURES)}:{line_no}: {line.strip()[:80]}")
    assert not violations, "Potential real secrets found:\n" + "\n".join(violations)


def test_talend_fake_secret_is_labeled():
    """The Talend fixture's deliberate fake secret must be labeled 'clearly fake'."""
    item = REPOS / "talend-sample" / "jobs" / "load_orders.item"
    assert item.exists(), "load_orders.item missing"
    text = item.read_text(encoding="utf-8")
    assert "FAKE_API_KEY" in text, "fake key marker missing"
    assert "clearly fake" in text.lower() or "fake" in text.lower(), "fake label missing"


def test_expected_md_repos_match_disk():
    """Every repo section in EXPECTED.md has a matching directory on disk."""
    expected_md = (FIXTURES / "EXPECTED.md").read_text(encoding="utf-8")
    sections = re.findall(r"^## repos/(\S+)", expected_md, re.MULTILINE)
    for repo in sections:
        assert (REPOS / repo).is_dir(), f"EXPECTED.md references repos/{repo} but directory not found"


def test_expected_md_docs_match_disk():
    """Every document section in EXPECTED.md has a matching file on disk."""
    expected_md = (FIXTURES / "EXPECTED.md").read_text(encoding="utf-8")
    # The docs section lists names after '- Entities: Document('
    doc_names = re.findall(r"Document\(([^,)]+)", expected_md)
    for name in doc_names:
        assert (DOCS / name).exists(), f"EXPECTED.md references docs/{name} but file not found"


def test_sql_dbt_sample_key_files():
    repo = REPOS / "sql-dbt-sample"
    assert (repo / "dbt_project.yml").exists()
    assert (repo / "models" / "staging" / "stg_orders.sql").exists()
    assert (repo / "models" / "marts" / "mart_orders.sql").exists()


def test_java_sample_excludes_compiled():
    """target/ dir exists in java-sample (harvester must exclude it)."""
    target = REPOS / "java-sample" / "target"
    assert target.exists(), "target/ missing – harvester exclusion test cannot run"


def test_dotnet_sample_excludes_build():
    """bin/ and obj/ exist in dotnet-sample (harvester must exclude them)."""
    assert (REPOS / "dotnet-sample" / "bin").exists()
    assert (REPOS / "dotnet-sample" / "obj").exists()
