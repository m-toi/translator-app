"""入力欄の文章を改行単位で翻訳する処理。"""

from dataclasses import dataclass

from .history import HistoryStore
from .models import TranslationEntry, TranslationMode
from .translator import VllmTranslator


@dataclass(frozen=True)
class LineTranslation:
    """画面に表示する1行分の翻訳結果。"""

    source_text: str
    translated_text: str


def translate_lines(
    source_text: str,
    translator: VllmTranslator,
    history_store: HistoryStore,
    source_lang: str,
    target_lang: str,
    mode: TranslationMode,
    conversation_id: str,
    relationship: str = "",
    speaker: str = "",
    force: bool = False,
    cached: dict[str, str] | None = None,
) -> tuple[list[LineTranslation], dict[str, str]]:
    """文章を改行で分割し、空行を除いて1行ずつ翻訳・保存する。"""
    results: list[LineTranslation] = []
    updated_cache = dict(cached or {})
    cache_prefix = "\0".join(
        [source_lang, target_lang, mode, conversation_id, relationship, speaker]
    )

    for raw_line in source_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        cache_key = f"{cache_prefix}\0{line}"
        if not force and cache_key in updated_cache:
            translated_text = updated_cache[cache_key]
        else:
            previous_entries = history_store.list_entries(conversation_id)
            translated_text = translator.translate(
                line,
                source_lang,
                target_lang,
                mode,
                history=previous_entries if mode == "conversation" else None,
                relationship=relationship,
                speaker=speaker,
            )
            history_store.add(
                TranslationEntry(
                    source_text=line,
                    translated_text=translated_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    mode=mode,
                    conversation_id=conversation_id,
                    relationship=relationship,
                    speaker=speaker,
                )
            )
            updated_cache[cache_key] = translated_text

        results.append(LineTranslation(line, translated_text))

    return results, updated_cache
