# Delta for git-normalize

## ADDED Requirements

### Requirement: Deterministic repository, module and owner extraction
The system SHALL extract `Repository`, `Module`, `Person` and `Team` entities and `OWNED_BY`/`DEPENDS_ON` edges from a repository's README, dependency manifests and `CODEOWNERS` file using deterministic parsing only, without calling an LLM, and SHALL emit values shaped to `harvesters.base.Entity`/`Edge` (Ontology v0: `type`, `name`, `external_id`, `props`, `source_id`, `ontology_version` on entities; `src_external_id`, `dst_external_id`, `relation`, `confidence`, `source_id`, `ontology_version` on edges).

#### Scenario: repository-from-readme
- **Given** a repo name and a README whose first line is `# Orders Service`
- **When** `extract_repository()` is called
- **Then** it returns one `Repository` entity with `external_id` `repo:<repo_name>` and `props["description"]` equal to `"Orders Service"`

#### Scenario: module-and-dependency-from-package-json
- **Given** a `package.json` with `"name": "orders-api"` and a `dependencies` object containing `"express"`
- **When** `extract_manifest_module()` is called
- **Then** it returns a `Module` entity `module:<repo_name>:orders-api`, a `Module` entity `module:express`, and a `DEPENDS_ON` edge from `orders-api`'s module to `express`'s module

#### Scenario: module-and-dependency-from-pom-xml
- **Given** a `pom.xml` with `<artifactId>orders-service</artifactId>` and one `<dependency>` with `<artifactId>spring-core</artifactId>`
- **When** `extract_manifest_module()` is called
- **Then** it returns a `Module` entity for `orders-service`, a `Module` entity for `spring-core`, and a `DEPENDS_ON` edge between them

#### Scenario: module-and-dependency-from-csproj
- **Given** a `SampleApp.csproj` with a `<PackageReference Include="Newtonsoft.Json" />`
- **When** `extract_manifest_module()` is called
- **Then** it returns a `Module` entity named `SampleApp` (from the filename), a `Module` entity for `Newtonsoft.Json`, and a `DEPENDS_ON` edge between them

#### Scenario: repo-level-dependency-from-requirements-txt
- **Given** a `requirements.txt` listing `requests==2.31.0`
- **When** `extract_manifest_module()` is called with the `Repository` entity
- **Then** no synthetic module entity is created for `requirements.txt` itself; a `Module` entity for `requests` is returned and a `DEPENDS_ON` edge runs from the `Repository` entity to it

#### Scenario: person-and-team-from-codeowners
- **Given** a `CODEOWNERS` file with lines `* @alice` and `/infra/ @myorg/platform-team`
- **When** `extract_owners()` is called
- **Then** it returns a `Person` entity `person:alice`, a `Team` entity `team:myorg/platform-team`, and one `OWNED_BY` edge from the `Repository` entity to each

#### Scenario: combined-normalize-repo
- **Given** a repo name, a README, one or more manifests and a `CODEOWNERS` file
- **When** `normalize_repo()` is called
- **Then** it returns the `Repository` entity, every `Module`/`Person`/`Team` entity de-duplicated by `external_id`, and every `OWNED_BY`/`DEPENDS_ON` edge from the steps above

#### Scenario: no-llm-call
- **Given** the same README, manifests and `CODEOWNERS` text
- **When** `normalize_repo()` is called twice
- **Then** both calls return identical entities and edges (deterministic, no external call)
