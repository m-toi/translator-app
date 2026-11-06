from translate_app.models import TranslationEntry
from translate_app.prompts import build_messages


def test_technical_prompt_explains_what_to_preserve():
    messages = build_messages("Run my_function()", "en", "ja", "technical")

    assert len(messages) == 1
    assert messages[-1] == {"role": "user", "content": "Run my_function()"}


def test_conversation_prompt_includes_relationship_and_history():
    history = [
        TranslationEntry(
            source_text="元の発言",
            translated_text="Previous translation",
            source_lang="ja",
            target_lang="en",
            mode="conversation",
        )
    ]

    messages = build_messages(
        "今回の発言",
        "ja",
        "en",
        "conversation",
        history=history,
        relationship="上司",
        speaker="自分",
    )

    assert messages == [
        {"role": "user", "content": "元の発言"},
        {"role": "assistant", "content": "Previous translation"},
        {"role": "user", "content": "今回の発言"},
    ]
