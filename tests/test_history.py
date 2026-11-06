from translate_app.history import JsonHistoryStore
from translate_app.models import TranslationEntry


def make_entry(number: int) -> TranslationEntry:
    return TranslationEntry(
        source_text=f"source {number}",
        translated_text=f"translation {number}",
        source_lang="ja",
        target_lang="en",
        mode="short",
    )


def test_json_history_removes_oldest_entries(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=2)

    store.add(make_entry(1))
    store.add(make_entry(2))
    store.add(make_entry(3))

    assert [entry.source_text for entry in store.list_entries()] == [
        "source 2",
        "source 3",
    ]


def test_json_history_keeps_conversation_filter(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=10)
    first = make_entry(1)
    second = make_entry(2)
    second.conversation_id = "other"
    store.add(first)
    store.add(second)

    assert store.list_entries("default") == [first]
    assert store.list_entries("other") == [second]


def test_json_history_deletes_entry_from_file(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=10)
    first = make_entry(1)
    second = make_entry(2)
    store.add(first)
    store.add(second)

    store.delete(first.entry_id)

    assert store.list_entries() == [second]
