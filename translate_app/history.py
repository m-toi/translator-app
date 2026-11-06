"""翻訳履歴の保存処理。

保存形式をこのモジュールに閉じ込めることで、将来JSONからSQLiteへ移行しやすくする。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .models import TranslationEntry


class HistoryStore(Protocol):
    """履歴保存先が満たす最小限のインターフェース。"""

    def list_entries(self, conversation_id: str | None = None) -> list[TranslationEntry]:
        ...

    def add(self, entry: TranslationEntry) -> None:
        ...


class HistoryStoreError(RuntimeError):
    """履歴ファイルを安全に読み書きできない場合のエラー。"""


class JsonHistoryStore:
    """やり取り数を上限にしてJSONへ履歴を保存する。"""

    def __init__(self, path: str | Path, max_entries: int = 100) -> None:
        if max_entries < 1:
            raise ValueError("max_entriesは1以上で指定してください")
        self.path = Path(path)
        self.max_entries = max_entries

    def list_entries(self, conversation_id: str | None = None) -> list[TranslationEntry]:
        entries = self._read()
        if conversation_id is None:
            return entries
        return [entry for entry in entries if entry.conversation_id == conversation_id]

    def add(self, entry: TranslationEntry) -> None:
        """新しい履歴を追加し、古いものから上限件数を超えて削除する。"""
        entries = self._read()
        entries.append(entry)
        # リストの先頭を古い履歴とすることで、FIFO削除を明確にする。
        entries = entries[-self.max_entries :]
        self._write(entries)

    def _read(self) -> list[TranslationEntry]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw_entries = json.load(file)
            if not isinstance(raw_entries, list):
                raise ValueError("JSONのトップレベルは配列である必要があります")
            return [TranslationEntry.from_dict(item) for item in raw_entries]
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise HistoryStoreError(f"履歴ファイルを読み込めません: {self.path}") from error

    def _write(self, entries: list[TranslationEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # 同じディレクトリ内で置換するため、途中状態や異なるディスク間の移動を避ける。
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(
                    [entry.to_dict() for entry in entries],
                    file,
                    ensure_ascii=False,
                    indent=2,
                )
                file.write("\n")
            os.replace(temporary_path, self.path)
        except OSError as error:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
            raise HistoryStoreError(f"履歴ファイルを保存できません: {self.path}") from error
