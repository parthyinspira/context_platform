"""Deterministic extraction of Repository/Module/Person/Team facts (KAN-14).

Parses a repository's README, dependency manifests (`package.json`, `pom.xml`,
`*.csproj`, `requirements.txt`) and `CODEOWNERS` file into Ontology v0
`Repository`, `Module`, `Person` and `Team` entities and `OWNED_BY` /
`DEPENDS_ON` edges, using only the standard library (`json`,
`xml.etree.ElementTree`) -- no LLM call, per `docs/HARVESTERS.md` rule 9.

This module is intentionally harvester-independent: no `GitHarvester` with a
working `connect`/`discover`/`harvest` exists yet (Epic 3), so
`normalize_repo()` is a plain function a future `GitHarvester.normalize()`
can call once it has fetched a repository's files, following the precedent
set by `ontology/sql_lineage.py` (KAN-25). Unlike that spike, the real
`harvesters.base.Entity`/`Edge` types now exist, so this module uses them
directly rather than defining its own.

Scope (see spec/changes/kan-14-normalize-repo-readme-manifests/proposal.md):
- CODEOWNERS ownership attaches to the Repository entity only, not to
  per-module paths (a future harvester has real file paths to resolve that).
- Manifest dependencies are name-only Module entities; no version/lockfile
  resolution.
"""
from __future__ import annotations

import json
import re
from typing import Literal
from xml.etree import ElementTree

from harvesters.base import Edge, Entity

ONTOLOGY_VERSION_DEFAULT = "v0"
DETERMINISTIC_CONFIDENCE = 1.0

CodeownersRule = tuple[str, list[str]]


def _repo_external_id(repo_name: str) -> str:
    return f"repo:{repo_name}"


def _module_external_id(repo_name: str, module_name: str) -> str:
    return f"module:{repo_name}:{module_name}"


def _dependency_external_id(dep_name: str) -> str:
    return f"module:{dep_name}"


def extract_repository(
    repo_name: str,
    source_id: str,
    readme_text: str | None = None,
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT,
) -> Entity:
    """Build the `Repository` entity, using the README's title as a description."""
    props: dict[str, str] = {}
    if readme_text:
        description = _readme_title(readme_text)
        if description:
            props["description"] = description

    return Entity(
        type="Repository",
        name=repo_name,
        external_id=_repo_external_id(repo_name),
        props=props,
        source_id=source_id,
        ontology_version=ontology_version,
    )


def _readme_title(readme_text: str) -> str | None:
    for line in readme_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.lstrip("#").strip()
    return None


def classify_owner(owner: str) -> Literal["Person", "Team"]:
    """GitHub CODEOWNERS convention: `@org/team` is a Team; anything else is a Person."""
    handle = owner.lstrip("@")
    return "Team" if "/" in handle else "Person"


def _owner_external_id(owner: str) -> str:
    handle = owner.lstrip("@")
    kind = classify_owner(owner)
    return f"team:{handle}" if kind == "Team" else f"person:{handle}"


def parse_codeowners(text: str) -> list[CodeownersRule]:
    """Parse a CODEOWNERS file into `(pattern, owners)` rules, skipping comments/blanks."""
    rules: list[CodeownersRule] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        pattern, owners = parts[0], parts[1:]
        if owners:
            rules.append((pattern, owners))
    return rules


def extract_owners(
    repo_entity: Entity,
    codeowners_text: str,
    source_id: str,
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT,
) -> tuple[list[Entity], list[Edge]]:
    """One Person/Team entity per distinct owner, one OWNED_BY edge per (repo, owner)."""
    entities: dict[str, Entity] = {}
    edges: dict[tuple[str, str], Edge] = {}

    for _pattern, owners in parse_codeowners(codeowners_text):
        for owner in owners:
            handle = owner.lstrip("@")
            kind = classify_owner(owner)
            external_id = _owner_external_id(owner)
            if external_id not in entities:
                entities[external_id] = Entity(
                    type=kind,
                    name=handle,
                    external_id=external_id,
                    source_id=source_id,
                    ontology_version=ontology_version,
                )
            edge_key = (repo_entity.external_id, external_id)
            if edge_key not in edges:
                edges[edge_key] = Edge(
                    src_external_id=repo_entity.external_id,
                    dst_external_id=external_id,
                    relation="OWNED_BY",
                    confidence=DETERMINISTIC_CONFIDENCE,
                    source_id=source_id,
                    ontology_version=ontology_version,
                )

    return list(entities.values()), list(edges.values())


def _depends_on_edges(
    src_external_id: str,
    dep_names: list[str],
    source_id: str,
    ontology_version: str,
) -> tuple[list[Entity], list[Edge]]:
    entities: list[Entity] = []
    edges: list[Edge] = []
    for dep_name in dep_names:
        dep_entity = Entity(
            type="Module",
            name=dep_name,
            external_id=_dependency_external_id(dep_name),
            source_id=source_id,
            ontology_version=ontology_version,
        )
        entities.append(dep_entity)
        edges.append(
            Edge(
                src_external_id=src_external_id,
                dst_external_id=dep_entity.external_id,
                relation="DEPENDS_ON",
                confidence=DETERMINISTIC_CONFIDENCE,
                source_id=source_id,
                ontology_version=ontology_version,
            )
        )
    return entities, edges


def _parse_package_json(text: str) -> tuple[str | None, list[str]]:
    data = json.loads(text)
    name = data.get("name")
    deps = list(data.get("dependencies", {}).keys())
    return name, deps


_POM_NS_RE = re.compile(r"^\{[^}]*\}")


def _local_tag(tag: str) -> str:
    return _POM_NS_RE.sub("", tag)


def _parse_pom_xml(text: str) -> tuple[str | None, list[str]]:
    root = ElementTree.fromstring(text)
    name = None
    deps: list[str] = []
    for child in root:
        if _local_tag(child.tag) == "artifactId":
            name = child.text.strip() if child.text else None
            break
    for dependency in root.iter():
        if _local_tag(dependency.tag) != "dependency":
            continue
        artifact_id = None
        for field in dependency:
            if _local_tag(field.tag) == "artifactId":
                artifact_id = field.text.strip() if field.text else None
                break
        if artifact_id:
            deps.append(artifact_id)
    return name, deps


def _parse_csproj(path: str, text: str) -> tuple[str | None, list[str]]:
    import os

    name = os.path.splitext(os.path.basename(path))[0]
    root = ElementTree.fromstring(text)
    deps: list[str] = []
    for ref in root.iter():
        if _local_tag(ref.tag) == "PackageReference":
            include = ref.get("Include")
            if include:
                deps.append(include)
    return name, deps


_REQUIREMENT_RE = re.compile(r"^[A-Za-z0-9_.\-]+")


def _parse_requirements_txt(text: str) -> list[str]:
    deps: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _REQUIREMENT_RE.match(stripped)
        if match:
            deps.append(match.group(0))
    return deps


def extract_manifest_module(
    path: str,
    text: str,
    repo_entity: Entity,
    source_id: str,
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT,
) -> tuple[Entity | None, list[Entity], list[Edge]]:
    """Parse one manifest file into a Module entity (if named) and its dependencies.

    `requirements.txt` declares no module name of its own: its dependencies
    attach directly to `repo_entity` instead of a synthetic module.
    """
    filename = path.rsplit("/", 1)[-1]

    if filename == "package.json":
        name, deps = _parse_package_json(text)
    elif filename == "pom.xml":
        name, deps = _parse_pom_xml(text)
    elif filename.endswith(".csproj"):
        name, deps = _parse_csproj(path, text)
    elif filename == "requirements.txt":
        deps = _parse_requirements_txt(text)
        dep_entities, dep_edges = _depends_on_edges(
            repo_entity.external_id, deps, source_id, ontology_version
        )
        return None, dep_entities, dep_edges
    else:
        raise ValueError(f"unsupported manifest file: {path}")

    if not name:
        raise ValueError(f"manifest at {path} declares no module name")

    module = Entity(
        type="Module",
        name=name,
        external_id=_module_external_id(repo_entity.name, name),
        source_id=source_id,
        ontology_version=ontology_version,
    )
    dep_entities, dep_edges = _depends_on_edges(
        module.external_id, deps, source_id, ontology_version
    )
    return module, dep_entities, dep_edges


def normalize_repo(
    source_id: str,
    repo_name: str,
    readme_text: str | None,
    manifests: list[tuple[str, str]],
    codeowners_text: str | None,
    ontology_version: str = ONTOLOGY_VERSION_DEFAULT,
) -> tuple[list[Entity], list[Edge]]:
    """Combine repository, owner and manifest extraction into one entity/edge set."""
    repo_entity = extract_repository(repo_name, source_id, readme_text, ontology_version)

    entities_by_id: dict[str, Entity] = {repo_entity.external_id: repo_entity}
    edges: list[Edge] = []

    if codeowners_text:
        owner_entities, owner_edges = extract_owners(
            repo_entity, codeowners_text, source_id, ontology_version
        )
        for entity in owner_entities:
            entities_by_id.setdefault(entity.external_id, entity)
        edges.extend(owner_edges)

    for path, text in manifests:
        module, dep_entities, dep_edges = extract_manifest_module(
            path, text, repo_entity, source_id, ontology_version
        )
        if module is not None:
            entities_by_id.setdefault(module.external_id, module)
        for entity in dep_entities:
            entities_by_id.setdefault(entity.external_id, entity)
        edges.extend(dep_edges)

    return list(entities_by_id.values()), edges
