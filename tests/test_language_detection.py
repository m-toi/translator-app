from translate_app.language_detection import looks_like_simplified_chinese


def test_detects_simplified_chinese_message():
    assert looks_like_simplified_chinese("你好，最近怎么样？")


def test_does_not_detect_japanese_message():
    assert not looks_like_simplified_chinese("こんにちは、元気ですか？")


def test_does_not_detect_short_ambiguous_text():
    assert not looks_like_simplified_chinese("東京")
