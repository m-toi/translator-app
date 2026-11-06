"""翻訳アプリで使うデータ型。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

LanguageCode = Literal["ja", "en", "zh"]
TranslationMode = Literal["short", "technical", "conversation"]


@dataclass
class TranslationEntry:
    """1回分の翻訳結果と、会話モードで使う補足情報。"""

    source_text: str
    translated_text: str
    source_lang: LanguageCode
    target_lang: LanguageCode
    mode: TranslationMode
    conversation_id: str = "default"
    relationship: str = ""
    speaker: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    entry_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, str]:
        """JSON保存用の辞書に変換する。"""
        return {
            "entry_id": self.entry_id,
            "created_at": self.created_at,
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "mode": self.mode,
            "conversation_id": self.conversation_id,
            "relationship": self.relationship,
            "speaker": self.speaker,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "TranslationEntry":
        """JSONから読み込んだ辞書を型付きデータに戻す。"""
        if not isinstance(data, dict):
            raise ValueError("履歴の各要素はJSONオブジェクトである必要があります")
        required = (
            "source_text",
            "translated_text",
            "source_lang",
            "target_lang",
            "mode",
        )
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise ValueError(f"履歴に必要な項目がありません: {', '.join(missing)}")

        return cls(
            entry_id=data.get("entry_id", str(uuid4())),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            source_text=data["source_text"],
            translated_text=data["translated_text"],
            source_lang=data["source_lang"],  # type: ignore[arg-type]
            target_lang=data["target_lang"],  # type: ignore[arg-type]
            mode=data["mode"],  # type: ignore[arg-type]
            conversation_id=data.get("conversation_id", "default"),
            relationship=data.get("relationship", ""),
            speaker=data.get("speaker", ""),
        )
