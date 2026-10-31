import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_PATH = ROOT / "scripts" / "generate_fixtures.py"

spec = importlib.util.spec_from_file_location("generate_fixtures", GEN_PATH)
generate_fixtures = importlib.util.module_from_spec(spec)
sys.modules["generate_fixtures"] = generate_fixtures
spec.loader.exec_module(generate_fixtures)


def _tree_hash(root: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_regeneration_is_deterministic(tmp_path):
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    generate_fixtures.generate(out1)
    generate_fixtures.generate(out2)
    assert _tree_hash(out1) == _tree_hash(out2)


def test_sql_dbt_fixture_present(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    repo = out / "repos" / "sql-dbt-sample"
    assert (repo / "models" / "staging" / "stg_orders.sql").is_file()
    assert (repo / "models" / "marts" / "mart_orders.sql").is_file()
    assert (repo / "seeds" / "source_orders.sql").is_file()
    assert (repo / "schema.yml").is_file()
    staging = (repo / "models" / "staging" / "stg_orders.sql").read_text()
    mart = (repo / "models" / "marts" / "mart_orders.sql").read_text()
    assert "source_orders" in staging
    assert "stg_orders" in mart


def test_java_fixture_present(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    repo = out / "repos" / "java-sample"
    assert (repo / "pom.xml").is_file()
    assert (repo / "src" / "main" / "java" / "com" / "inspira" / "sample" / "OrdersRepository.java").is_file()
    assert (repo / "src" / "main" / "resources" / "orders.sql").is_file()
    assert (repo / "target" / "classes" / "OrdersRepository.class").is_file()


def test_dotnet_fixture_present(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    repo = out / "repos" / "dotnet-sample"
    assert (repo / "SampleApp.sln").is_file()
    assert (repo / "SampleApp.csproj").is_file()
    assert (repo / "OrdersService.cs").is_file()
    assert (repo / "appsettings.json").is_file()
    assert (repo / "bin" / "Debug" / "SampleApp.dll").is_file()
    assert (repo / "obj" / "SampleApp.csproj.nuget.g.props").is_file()


def test_talend_fixture_present_with_size_cap_violation(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    repo = out / "repos" / "talend-sample"
    item = repo / "jobs" / "load_orders.item"
    props = repo / "jobs" / "load_orders.properties"
    screenshot = repo / "screenshots" / "load_orders.png"
    assert item.is_file()
    assert props.is_file()
    assert screenshot.is_file()
    size_cap_bytes = 1024 * 1024
    assert screenshot.stat().st_size > size_cap_bytes


def test_talend_fake_secret_is_clearly_fake(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    item_text = (out / "repos" / "talend-sample" / "jobs" / "load_orders.item").read_text()
    assert "FAKE_API_KEY=sk-fake-0000000000000000" in item_text


def test_postgres_fixture_present(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    sql = (out / "db" / "init.sql").read_text()
    assert "CREATE SCHEMA" in sql
    assert "CREATE TABLE" in sql
    assert "CREATE VIEW" in sql
    assert "CREATE OR REPLACE PROCEDURE" in sql or "CREATE FUNCTION" in sql
    assert "source_orders" in sql
    assert "is_stale" in sql or "stale" in sql.lower()


def test_docs_and_excel_fixture_present(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    docs = out / "docs"
    policy = docs / "data-retention-policy.md"
    faq = docs / "orders-faq.md"
    excel = docs / "sample_report.xlsx"
    assert policy.is_file()
    assert faq.is_file()
    assert excel.is_file()
    policy_text = policy.read_text()
    faq_text = faq.read_text()
    assert "sensitivity: restricted" in policy_text
    assert "sensitivity: internal" in faq_text


def test_expected_md_documents_entities(tmp_path):
    out = tmp_path / "fixtures"
    generate_fixtures.generate(out)
    expected = (out / "EXPECTED.md").read_text()
    for name in ("Repository", "Table", "Job", "Document"):
        assert name in expected
