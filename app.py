"""Streamlitで動かすローカル翻訳画面。"""

from pathlib import Path

import streamlit as st

from translate_app.history import HistoryStoreError, JsonHistoryStore
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

if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "last_observed_input" not in st.session_state:
    st.session_state.last_observed_input = ""
if "pending_translation" not in st.session_state:
    st.session_state.pending_translation = False


def handle_text_change() -> None:
    """改行が追加されたときだけ翻訳を予約する。"""
    text = st.session_state.source_text
    if text.count("\n") > st.session_state.last_observed_input.count("\n"):
        st.session_state.pending_translation = True
    st.session_state.last_observed_input = text


def swap_languages() -> None:
    """原文と翻訳先を入れ替える。Selectbox生成前のコールバックで実行する。"""
    source_lang = st.session_state.source_lang
    st.session_state.source_lang = st.session_state.target_lang
    st.session_state.target_lang = source_lang


with st.sidebar:
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

st.subheader("翻訳する言語")
language_column, swap_column, target_column = st.columns([5, 1, 5])
with language_column:
    source_lang = st.selectbox(
        "原文の言語",
        options=list(language_names),
        format_func=lambda code: language_names[code],
        key="source_lang",
    )
with swap_column:
    st.write("")
    st.button(
        "⇄",
        help="原文の言語と翻訳先の言語を入れ替えます",
        on_click=swap_languages,
    )
with target_column:
    target_lang = st.selectbox(
        "翻訳先の言語",
        options=list(language_names),
        format_func=lambda code: language_names[code],
        key="target_lang",
    )

source_text = st.text_area(
    "翻訳する文章（改行ごとに1件として翻訳・保存）",
    height=180,
    help="改行するか、下の「翻訳する」ボタンを押したときに翻訳します。",
    key="source_text",
    on_change=handle_text_change,
)
source_lang = st.session_state.source_lang
target_lang = st.session_state.target_lang

if "translated_lines" not in st.session_state:
    st.session_state.translated_lines = {}
if "last_input" not in st.session_state:
    st.session_state.last_input = ""
if "displayed_results" not in st.session_state:
    st.session_state.displayed_results = []

manual_translate = st.button(
    "翻訳する",
    type="primary",
    disabled=not source_text.strip(),
)

should_translate = (
    source_text.strip()
    and (st.session_state.pending_translation or manual_translate)
)
if should_translate:
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
            # ボタンは明示的な再翻訳、改行は未処理行の翻訳として扱う。
            force=manual_translate,
            cached=st.session_state.translated_lines,
        )
        st.session_state.translated_lines = cached_lines
        st.session_state.last_input = source_text
        st.session_state.displayed_results = translated_lines
        st.session_state.pending_translation = False
    except (HistoryStoreError, RuntimeError) as error:
        # 接続エラーや履歴の破損を画面に明示し、成功したように見せない。
        st.session_state.last_input = ""
        st.error(f"翻訳に失敗しました: {error}")

if st.session_state.displayed_results:
    st.subheader("翻訳結果")
    for result in st.session_state.displayed_results:
        st.markdown(f"**原文**: {result.source_text}")
        st.markdown(f"**訳文**: {result.translated_text}")

with st.expander("この会話の履歴"):
    entries = history_store.list_entries(conversation_id)
    if not entries:
        st.info("まだ履歴はありません。")
    elif mode == "conversation":
        st.caption(
            "以下の履歴は、次回の会話翻訳で前後関係を読むために使用されます。"
        )
    for entry in reversed(entries):
        history_column, delete_column = st.columns([8, 1])
        with history_column:
            st.markdown(
                f"**{entry.speaker or '話者未指定'} / "
                f"{entry.source_lang}→{entry.target_lang}**"
            )
            st.markdown(f"**原文**\n\n{entry.source_text}")
            st.markdown(f"**訳文**\n\n{entry.translated_text}")
        with delete_column:
            if st.button("削除", key=f"delete-history-{entry.entry_id}"):
                try:
                    history_store.delete(entry.entry_id)
                    st.session_state.translated_lines = {}
                    st.session_state.displayed_results = []
                    st.rerun()
                except HistoryStoreError as error:
                    st.error(str(error))
        st.divider()
