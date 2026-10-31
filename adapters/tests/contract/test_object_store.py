from adapters.object_store.local import LocalObjectStore


def test_put_get_list_delete(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)

    store.put("raw/file1.txt", b"hello")

    assert store.list() == ["raw/file1.txt"]
    assert store.list(prefix="raw/") == ["raw/file1.txt"]
    assert store.list(prefix="other/") == []
    assert store.get("raw/file1.txt") == b"hello"

    store.delete("raw/file1.txt")

    assert store.list() == []


def test_key_cannot_escape_root(tmp_path) -> None:
    store = LocalObjectStore(tmp_path)

    try:
        store.put("../escape.txt", b"nope")
        assert False, "expected ValueError"
    except ValueError:
        pass
