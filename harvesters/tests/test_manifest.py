"""Tests for KAN-77 manifest recording (harvesters/manifest.py).

Scenarios map to spec/changes/kan-77-manifest-recording/specs/harvester-framework.md.
"""
from datetime import UTC, datetime
from pathlib import Path

import pytest

from adapters.object_store import LocalObjectStore
from harvesters.framework.manifest import (
    Manifest,
    ManifestError,
    ManifestStore,
    Outcome,
)

SOURCE_ID = "11111111-1111-1111-1111-111111111111"
RUN_ID = "run-0001"
FIXED_NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


def _manifest() -> Manifest:
    return Manifest(source_id=SOURCE_ID, run_id=RUN_ID, now=lambda: FIXED_NOW)


def _populated() -> Manifest:
    m = _manifest()
    m.discovered("models/stg_orders.sql", reason="listed by ls-tree", size_bytes=512)
    m.discovered("models/mart_orders.sql", reason="listed by ls-tree", size_bytes=640)
    m.discovered("target/app.jar", reason="listed by ls-tree", size_bytes=5_000_000)
    m.discovered("models/broken.sql", reason="listed by ls-tree", size_bytes=10)
    m.discovered("models/pending.sql", reason="listed by ls-tree", size_bytes=20)
    m.fetched("models/stg_orders.sql", reason="matched include models/**/*.sql")
    m.fetched("models/mart_orders.sql", reason="matched include models/**/*.sql")
    m.skipped("target/app.jar", reason="excluded: build output target/")
    m.failed("models/broken.sql", reason="fetch error: blob not found")
    return m


# Scenario: record every outcome with reason
def test_records_every_outcome_with_reason():
    m = _populated()

    stg = m.get("models/stg_orders.sql")
    assert stg.outcome is Outcome.FETCHED
    assert stg.discovery_reason == "listed by ls-tree"
    assert stg.outcome_reason == "matched include models/**/*.sql"
    assert stg.size_bytes == 512
    assert stg.discovered_at == FIXED_NOW and stg.outcome_at == FIXED_NOW

    jar = m.get("target/app.jar")
    assert jar.outcome is Outcome.SKIPPED
    assert jar.outcome_reason == "excluded: build output target/"

    broken = m.get("models/broken.sql")
    assert broken.outcome is Outcome.FAILED
    assert broken.outcome_reason == "fetch error: blob not found"

    pending = m.get("models/pending.sql")
    assert pending.outcome is None
    assert pending.status == "discovered"
    assert len(m.entries()) == 5


def test_size_is_optional():
    m = _manifest()
    m.discovered("README.md", reason="listed by ls-tree")
    assert m.get("README.md").size_bytes is None


# Scenario: reason required
@pytest.mark.parametrize("reason", ["", "   ", None])
def test_discovered_requires_reason(reason):
    m = _manifest()
    with pytest.raises(ManifestError):
        m.discovered("a.sql", reason=reason)
    assert m.entries() == []


@pytest.mark.parametrize("method", ["fetched", "skipped", "failed"])
@pytest.mark.parametrize("reason", ["", "  \t"])
def test_outcome_requires_reason(method, reason):
    m = _manifest()
    m.discovered("a.sql", reason="listed")
    with pytest.raises(ManifestError):
        getattr(m, method)("a.sql", reason=reason)
    assert m.get("a.sql").outcome is None


def test_ref_required():
    m = _manifest()
    with pytest.raises(ManifestError):
        m.discovered("  ", reason="listed")


def test_negative_size_rejected():
    m = _manifest()
    with pytest.raises(ManifestError):
        m.discovered("a.sql", reason="listed", size_bytes=-1)


# Scenario: discover before outcome
@pytest.mark.parametrize("method", ["fetched", "skipped", "failed"])
def test_outcome_requires_prior_discovery(method):
    m = _manifest()
    with pytest.raises(ManifestError, match="not discovered"):
        getattr(m, method)("a.sql", reason="some reason")
    assert m.entries() == []


# Scenario: one outcome per object
def test_conflicting_outcome_rejected():
    m = _manifest()
    m.discovered("a.sql", reason="listed")
    m.skipped("a.sql", reason="over 1 MB size cap")
    with pytest.raises(ManifestError, match="already"):
        m.fetched("a.sql", reason="matched include")
    with pytest.raises(ManifestError):
        m.skipped("a.sql", reason="a different reason")
    assert m.get("a.sql").outcome is Outcome.SKIPPED
    assert m.get("a.sql").outcome_reason == "over 1 MB size cap"


def test_identical_records_are_idempotent():
    m = _manifest()
    m.discovered("a.sql", reason="listed", size_bytes=3)
    m.discovered("a.sql", reason="listed", size_bytes=3)
    m.skipped("a.sql", reason="over 1 MB size cap")
    m.skipped("a.sql", reason="over 1 MB size cap")
    assert len(m.entries()) == 1
    assert m.get("a.sql").outcome is Outcome.SKIPPED


def test_conflicting_rediscovery_rejected():
    m = _manifest()
    m.discovered("a.sql", reason="listed", size_bytes=3)
    with pytest.raises(ManifestError):
        m.discovered("a.sql", reason="listed", size_bytes=4)


# Scenario: secret in a reason is redacted
def test_secret_in_reason_is_redacted():
    # Clearly fake credential, seeded only to prove redaction.
    fake_password = "fakepass-not-real-123"
    m = _manifest()
    m.discovered("db/catalog", reason="listed by catalog query")
    m.failed(
        "db/catalog",
        reason=f"connect failed: postgresql://reader:{fake_password}@db:5432/demo",
    )
    stored = m.get("db/catalog").outcome_reason
    assert fake_password not in stored
    assert "[REDACTED:" in stored
    assert fake_password not in m.to_json()


def test_secret_in_discovery_reason_is_redacted():
    fake_key = "AKIAFAKEEXAMPLE12345"  # clearly fake, AWS-shaped
    m = _manifest()
    m.discovered("x.cfg", reason=f"listed with key {fake_key}")
    assert fake_key not in m.get("x.cfg").discovery_reason


# Scenario: validator reads outcomes and unaccounted objects
def test_validator_reads_outcomes_counts_and_unaccounted():
    m = _populated()

    fetched = m.by_outcome(Outcome.FETCHED)
    assert [e.ref for e in fetched] == ["models/mart_orders.sql", "models/stg_orders.sql"]
    assert [e.ref for e in m.by_outcome(Outcome.SKIPPED)] == ["target/app.jar"]
    failed = m.by_outcome(Outcome.FAILED)
    assert [(e.ref, e.outcome_reason) for e in failed] == [
        ("models/broken.sql", "fetch error: blob not found")
    ]

    assert m.counts() == {
        "discovered": 5,
        "fetched": 2,
        "skipped": 1,
        "failed": 1,
        "unaccounted": 1,
    }
    assert [e.ref for e in m.unaccounted()] == ["models/pending.sql"]


def test_entries_are_sorted_by_ref():
    m = _populated()
    refs = [e.ref for e in m.entries()]
    assert refs == sorted(refs)


def test_empty_manifest_counts():
    assert _manifest().counts() == {
        "discovered": 0,
        "fetched": 0,
        "skipped": 0,
        "failed": 0,
        "unaccounted": 0,
    }


# Scenario: manifest persisted and reloaded per run
def test_manifest_persisted_and_reloaded(tmp_path):
    object_store = LocalObjectStore(tmp_path)
    store = ManifestStore(object_store)
    m = _populated()

    key = store.save(m)
    assert key == f"manifests/{SOURCE_ID}/{RUN_ID}.json"
    assert object_store.list("manifests/") == [key]

    loaded = store.load(SOURCE_ID, RUN_ID)
    assert loaded.source_id == SOURCE_ID
    assert loaded.run_id == RUN_ID
    assert loaded.entries() == m.entries()
    assert loaded.counts() == m.counts()


def test_json_round_trip_is_stable():
    m = _populated()
    text = m.to_json()
    again = Manifest.from_json(text)
    assert again.to_json() == text
    assert again.entries() == m.entries()


def test_reloaded_manifest_keeps_rules():
    m = Manifest.from_json(_populated().to_json())
    with pytest.raises(ManifestError):
        m.fetched("target/app.jar", reason="matched include")
    m.fetched("models/pending.sql", reason="matched include models/**/*.sql")
    assert m.unaccounted() == []


def _raw_entry(**overrides) -> dict:
    entry = {
        "ref": "a.sql",
        "discovery_reason": "listed",
        "discovered_at": FIXED_NOW.isoformat(),
        "size_bytes": 1,
        "outcome": "fetched",
        "outcome_reason": "matched include",
        "outcome_at": FIXED_NOW.isoformat(),
    }
    entry.update(overrides)
    return entry


def _raw_manifest(*entries: dict) -> dict:
    return {
        "format_version": 1,
        "source_id": SOURCE_ID,
        "run_id": RUN_ID,
        "entries": list(entries),
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"discovery_reason": ""},
        {"discovery_reason": None},
        {"outcome_reason": None},
        {"outcome_reason": "  "},
        {"outcome": None, "outcome_reason": "orphan reason", "outcome_at": None},
        {"ref": ""},
        {"size_bytes": -5},
        {"size_bytes": True},
        {"outcome": "deleted"},
        {"discovered_at": "not-a-date"},
    ],
)
def test_loading_enforces_recording_rules(overrides):
    with pytest.raises(ManifestError):
        Manifest.from_dict(_raw_manifest(_raw_entry(**overrides)))


@pytest.mark.parametrize(
    "data",
    [
        {"format_version": 1, "source_id": SOURCE_ID, "run_id": RUN_ID},  # no entries
        _raw_manifest({"ref": "a.sql", "discovery_reason": "listed"}),  # no discovered_at
        _raw_manifest("not-a-dict"),
        "not-a-dict",
    ],
)
def test_malformed_file_raises_manifest_error(data):
    with pytest.raises(ManifestError):
        Manifest.from_dict(data)


def test_discovered_rejects_bool_size():
    m = _manifest()
    with pytest.raises(ManifestError):
        m.discovered("a.sql", reason="listed", size_bytes=True)


def test_loading_rejects_duplicate_refs():
    with pytest.raises(ManifestError, match="duplicate"):
        Manifest.from_dict(_raw_manifest(_raw_entry(), _raw_entry()))


def test_loading_redacts_secrets_in_reasons():
    fake_password = "fakepass-not-real-456"  # clearly fake, seeded for redaction
    raw = _raw_manifest(
        _raw_entry(outcome="failed", outcome_reason=f"dsn postgresql://u:{fake_password}@h/db")
    )
    loaded = Manifest.from_dict(raw)
    assert fake_password not in loaded.get("a.sql").outcome_reason
    assert fake_password not in loaded.to_json()


def test_store_load_rejects_mismatched_ids(tmp_path):
    object_store = LocalObjectStore(tmp_path)
    other = Manifest(source_id="other-source", run_id="other-run")
    object_store.put(ManifestStore.key(SOURCE_ID, RUN_ID), other.to_json().encode("utf-8"))
    with pytest.raises(ManifestError, match="does not match"):
        ManifestStore(object_store).load(SOURCE_ID, RUN_ID)


def test_store_load_forwards_clock(tmp_path):
    store = ManifestStore(LocalObjectStore(tmp_path))
    m = _manifest()
    m.discovered("a.sql", reason="listed")
    store.save(m)
    later = datetime(2026, 11, 1, tzinfo=UTC)
    loaded = store.load(SOURCE_ID, RUN_ID, now=lambda: later)
    assert loaded.fetched("a.sql", reason="matched include").outcome_at == later


# End to end on a real fixture repo: walk, record, persist, reload, read.
def test_end_to_end_on_java_fixture(tmp_path):
    repo = Path(__file__).resolve().parents[2] / "fixtures" / "repos" / "java-sample"
    m = Manifest(source_id="java-sample", run_id="e2e-1", now=lambda: FIXED_NOW)
    files = sorted(p for p in repo.rglob("*") if p.is_file())
    for p in files:
        rel = p.relative_to(repo).as_posix()
        m.discovered(rel, reason="listed by filesystem walk", size_bytes=p.stat().st_size)
        if rel.startswith("target/"):
            m.skipped(rel, reason="excluded: build output target/")
        else:
            m.fetched(rel, reason="matched java stack include")

    store = ManifestStore(LocalObjectStore(tmp_path))
    store.save(m)
    loaded = store.load("java-sample", "e2e-1")

    skipped = loaded.by_outcome(Outcome.SKIPPED)
    assert skipped and all(e.ref.startswith("target/") for e in skipped)
    assert all(e.outcome_reason == "excluded: build output target/" for e in skipped)
    counts = loaded.counts()
    assert counts["discovered"] == len(files)
    assert counts["fetched"] + counts["skipped"] == len(files)
    assert counts["unaccounted"] == 0


@pytest.mark.parametrize("bad", ["../x", "a/b", ""])
def test_store_rejects_unsafe_ids(tmp_path, bad):
    store = ManifestStore(LocalObjectStore(tmp_path))
    with pytest.raises(ManifestError):
        store.load(SOURCE_ID, bad)
    with pytest.raises(ManifestError):
        Manifest(source_id=bad or " ", run_id=RUN_ID)
