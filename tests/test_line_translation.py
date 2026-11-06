from translate_app.history import JsonHistoryStore
from translate_app.line_translation import translate_lines


class FakeTranslator:
    def translate(self, source_text, *args, **kwargs):
        return f"translated: {source_text}"


def test_translate_lines_saves_each_non_empty_line(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=10)

    results, _ = translate_lines(
        "first\n\nsecond",
        FakeTranslator(),
        store,
        "en",
        "ja",
        "short",
        "default",
    )

    assert [result.translated_text for result in results] == [
        "translated: first",
        "translated: second",
    ]
    assert [entry.source_text for entry in store.list_entries()] == ["first", "second"]


def test_translate_lines_reuses_cached_lines(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=10)

    results, cache = translate_lines(
        "same",
        FakeTranslator(),
        store,
        "en",
        "ja",
        "short",
        "default",
    )
    second_results, _ = translate_lines(
        "same",
        FakeTranslator(),
        store,
        "en",
        "ja",
        "short",
        "default",
        cached=cache,
    )

    assert results == second_results
    assert len(store.list_entries()) == 1


def test_translate_lines_does_not_reuse_cache_for_different_target(tmp_path):
    store = JsonHistoryStore(tmp_path / "history.json", max_entries=10)

    _, cache = translate_lines(
        "same",
        FakeTranslator(),
        store,
        "en",
        "ja",
        "short",
        "default",
    )
    translate_lines(
        "same",
        FakeTranslator(),
        store,
        "en",
        "zh",
        "short",
        "default",
        cached=cache,
    )

    assert len(store.list_entries()) == 2
