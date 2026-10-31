from pathlib import Path

from harvesters.base import Edge, Entity
from harvesters.git.normalize import (
    classify_owner,
    extract_manifest_module,
    extract_owners,
    extract_repository,
    normalize_repo,
    parse_codeowners,
)

FIXTURES = Path(__file__).resolve().parent.parent / "git" / "fixtures"
SOURCE_ID = "src-1"
REPO_NAME = "orders-service"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_repository_from_readme():
    readme = _read("README.md")

    repo = extract_repository(REPO_NAME, SOURCE_ID, readme_text=readme)

    assert isinstance(repo, Entity)
    assert repo.type == "Repository"
    assert repo.name == REPO_NAME
    assert repo.external_id == f"repo:{REPO_NAME}"
    assert repo.source_id == SOURCE_ID
    assert repo.props["description"] == "Orders Service"


def test_repository_without_readme_has_no_description():
    repo = extract_repository(REPO_NAME, SOURCE_ID, readme_text=None)

    assert "description" not in repo.props


def test_classify_owner():
    assert classify_owner("@myorg/platform-team") == "Team"
    assert classify_owner("@alice") == "Person"
    assert classify_owner("bob@example.com") == "Person"


def test_parse_codeowners():
    rules = parse_codeowners(_read("CODEOWNERS"))

    assert rules == [
        ("*", ["@alice"]),
        ("/infra/", ["@myorg/platform-team"]),
        ("/docs/", ["@bob", "@myorg/docs-team"]),
    ]


def test_person_and_team_from_codeowners():
    repo = extract_repository(REPO_NAME, SOURCE_ID)

    entities, edges = extract_owners(repo, _read("CODEOWNERS"), SOURCE_ID)

    by_id = {e.external_id: e for e in entities}
    assert by_id["person:alice"].type == "Person"
    assert by_id["person:bob"].type == "Person"
    assert by_id["team:myorg/platform-team"].type == "Team"
    assert by_id["team:myorg/docs-team"].type == "Team"
    assert len(entities) == 4

    owned_by = [e for e in edges if e.relation == "OWNED_BY"]
    assert len(owned_by) == 4
    for edge in owned_by:
        assert isinstance(edge, Edge)
        assert edge.src_external_id == repo.external_id
        assert edge.relation == "OWNED_BY"
        assert edge.source_id == SOURCE_ID
    dsts = {e.dst_external_id for e in owned_by}
    assert dsts == {
        "person:alice",
        "person:bob",
        "team:myorg/platform-team",
        "team:myorg/docs-team",
    }


def test_module_and_dependency_from_package_json():
    repo = extract_repository(REPO_NAME, SOURCE_ID)

    module, entities, edges = extract_manifest_module(
        "package.json", _read("package.json"), repo, SOURCE_ID
    )

    assert module is not None
    assert module.type == "Module"
    assert module.name == "orders-api"
    assert module.external_id == f"module:{REPO_NAME}:orders-api"

    dep_ids = {e.external_id for e in entities if e.external_id != module.external_id}
    assert dep_ids == {"module:express", "module:pg"}

    depends_on = [e for e in edges if e.relation == "DEPENDS_ON"]
    assert {e.dst_external_id for e in depends_on} == {"module:express", "module:pg"}
    assert all(e.src_external_id == module.external_id for e in depends_on)


def test_module_and_dependency_from_pom_xml():
    repo = extract_repository(REPO_NAME, SOURCE_ID)

    module, entities, edges = extract_manifest_module("pom.xml", _read("pom.xml"), repo, SOURCE_ID)

    assert module.name == "orders-service"
    assert module.external_id == f"module:{REPO_NAME}:orders-service"
    dep_ids = {e.dst_external_id for e in edges if e.relation == "DEPENDS_ON"}
    assert dep_ids == {"module:spring-core", "module:postgresql"}


def test_module_and_dependency_from_csproj():
    repo = extract_repository(REPO_NAME, SOURCE_ID)

    module, entities, edges = extract_manifest_module(
        "SampleApp.csproj", _read("SampleApp.csproj"), repo, SOURCE_ID
    )

    assert module.name == "SampleApp"
    assert module.external_id == f"module:{REPO_NAME}:SampleApp"
    dep_ids = {e.dst_external_id for e in edges if e.relation == "DEPENDS_ON"}
    assert dep_ids == {"module:Newtonsoft.Json", "module:Npgsql"}


def test_repo_level_dependency_from_requirements_txt():
    repo = extract_repository(REPO_NAME, SOURCE_ID)

    module, entities, edges = extract_manifest_module(
        "requirements.txt", _read("requirements.txt"), repo, SOURCE_ID
    )

    assert module is None
    dep_ids = {e.external_id for e in entities}
    assert dep_ids == {"module:requests", "module:pydantic", "module:click"}

    depends_on = [e for e in edges if e.relation == "DEPENDS_ON"]
    assert all(e.src_external_id == repo.external_id for e in depends_on)
    assert {e.dst_external_id for e in depends_on} == {
        "module:requests",
        "module:pydantic",
        "module:click",
    }


def test_combined_normalize_repo():
    entities, edges = normalize_repo(
        source_id=SOURCE_ID,
        repo_name=REPO_NAME,
        readme_text=_read("README.md"),
        manifests=[
            ("package.json", _read("package.json")),
            ("requirements.txt", _read("requirements.txt")),
        ],
        codeowners_text=_read("CODEOWNERS"),
    )

    types = {e.type for e in entities}
    assert types == {"Repository", "Module", "Person", "Team"}

    external_ids = [e.external_id for e in entities]
    assert len(external_ids) == len(set(external_ids))  # no duplicates

    relations = {e.relation for e in edges}
    assert relations == {"OWNED_BY", "DEPENDS_ON"}


def test_normalize_repo_is_deterministic():
    kwargs = dict(
        source_id=SOURCE_ID,
        repo_name=REPO_NAME,
        readme_text=_read("README.md"),
        manifests=[
            ("package.json", _read("package.json")),
            ("pom.xml", _read("pom.xml")),
            ("SampleApp.csproj", _read("SampleApp.csproj")),
            ("requirements.txt", _read("requirements.txt")),
        ],
        codeowners_text=_read("CODEOWNERS"),
    )

    first = normalize_repo(**kwargs)
    second = normalize_repo(**kwargs)

    assert first == second
