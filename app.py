"""Streamlitで動かすローカル翻訳画面。"""

from pathlib import Path

import streamlit as st

from translate_app.history import HistoryStoreError, JsonHistoryStore
from translate_app.language_detection import looks_like_simplified_chinese
from translate_app.line_translation import translate_lines
from translate_app.translator import VllmTranslator

st.set_page_config(page_title="ローカル翻訳", page_icon="翻")
st.title("ローカル翻訳")
st.caption("PLaMo 3 Translate 8B W4A16 / vLLM")

language_names = {"ja": "日本語", "en": "英語", "zh": "中国語（簡体字）"}
mode_names = {
    "short": "短文翻訳",
    "technical": "技術翻訳",
    "conversation": "会話翻訳",
}

if "source_lang" not in st.session_state:
    st.session_state.source_lang = "ja"
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "en"
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "language_manual_override" not in st.session_state:
    st.session_state.language_manual_override = False
if "auto_detected_languages" not in st.session_state:
    st.session_state.auto_detected_languages = ("ja", "en")
if "chinese_detection_message" not in st.session_state:
    st.session_state.chinese_detection_message = ""


def detect_pasted_language() -> None:
    """文章欄の変更時に、中国語なら言語設定を自動更新する。"""
    text = st.session_state.source_text
    if (
        looks_like_simplified_chinese(text)
        and not st.session_state.language_manual_override
    ):
        st.session_state.source_lang = "zh"
        st.session_state.target_lang = "ja"
        st.session_state.auto_detected_languages = ("zh", "ja")
        st.session_state.chinese_detection_message = (
            "中国語（簡体字）を検出したため、日本語へ自動翻訳します。"
        )
    elif text and not looks_like_simplified_chinese(text):
        st.session_state.chinese_detection_message = ""


with st.sidebar:
    source_lang = st.selectbox(
        "原文の言語",
        options=list(language_names),
        format_func=lambda code: language_names[code],
        key="source_lang",
    )
    target_lang = st.selectbox(
        "翻訳先の言語",
        options=list(language_names),
        index=1,
        format_func=lambda code: language_names[code],
        key="target_lang",
    )
    if (
        (source_lang, target_lang) != st.session_state.auto_detected_languages
        and st.session_state.chinese_detection_message
    ):
        st.session_state.language_manual_override = True
    if st.button("言語の自動判定を再開"):
        st.session_state.language_manual_override = False
        st.session_state.chinese_detection_message = ""
        st.rerun()
    mode = st.selectbox(
        "翻訳モード",
        options=list(mode_names),
        format_func=lambda value: mode_names[value],
    )
    conversation_id = st.text_input("会話ID", value="default")
    relationship = st.text_input("相手との関係", disabled=mode != "conversation")
    max_history = st.number_input(
        "保存する最大やり取り数",
        min_value=1,
        max_value=10000,
        value=100,
        step=1,
    )

history_store = JsonHistoryStore(Path("data/history.json"), int(max_history))
if mode == "conversation":
    # 入力した発言が誰のものかを、翻訳前に明示できるようにする。
    speaker = st.radio(
        "この発言をした人",
        options=["自分", "相手"],
        horizontal=True,
        key="conversation_speaker",
    )
else:
    speaker = ""
source_text = st.text_area(
    "翻訳する文章（改行ごとに1件として翻訳・保存）",
    height=180,
    help="入力欄の変更が確定すると自動翻訳します。複数行は行ごとに処理します。",
    key="source_text",
    on_change=detect_pasted_language,
)
source_lang = st.session_state.source_lang
target_lang = st.session_state.target_lang
if st.session_state.chinese_detection_message:
    st.info(st.session_state.chinese_detection_message)

if "translated_lines" not in st.session_state:
    st.session_state.translated_lines = {}
if "last_input" not in st.session_state:
    st.session_state.last_input = ""
if "last_settings" not in st.session_state:
    st.session_state.last_settings = ()

input_changed = source_text != st.session_state.last_input
settings = (
    source_lang,
    target_lang,
    mode,
    conversation_id,
    relationship,
    speaker,
)
settings_changed = settings != st.session_state.last_settings
manual_translate = st.button(
    "もう一度翻訳する",
    type="primary",
    disabled=not source_text.strip(),
)

if source_text.strip() and (input_changed or settings_changed or manual_translate):
    translator = VllmTranslator()
    try:
        translated_lines, cached_lines = translate_lines(
            source_text,
            translator,
            history_store,
            source_lang,
            target_lang,
            mode,
            conversation_id,
            relationship,
            speaker,
            force=manual_translate,
            cached=st.session_state.translated_lines,
        )
        st.session_state.translated_lines = cached_lines
        st.session_state.last_input = source_text
        st.session_state.last_settings = settings
        st.subheader("翻訳結果")
        for result in translated_lines:
            st.markdown(f"**原文**: {result.source_text}")
            st.markdown(f"**訳文**: {result.translated_text}")
    except (HistoryStoreError, RuntimeError) as error:
        # 接続エラーや履歴の破損を画面に明示し、成功したように見せない。
        st.session_state.last_input = ""
        st.error(f"翻訳に失敗しました: {error}")

with st.expander("この会話の履歴"):
    entries = history_store.list_entries(conversation_id)
    if not entries:
        st.info("まだ履歴はありません。")
    for entry in reversed(entries):
        st.markdown(f"**原文**\n\n{entry.source_text}")
        st.markdown(f"**訳文**\n\n{entry.translated_text}")
        st.divider()
