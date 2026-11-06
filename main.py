"""ローカル翻訳CLIのエントリーポイント。"""

import argparse
from pathlib import Path

from translate_app.history import JsonHistoryStore
from translate_app.models import TranslationEntry
from translate_app.translator import VllmTranslator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PLaMo 3 Translateを使うローカル翻訳")
    parser.add_argument("text", help="翻訳する文章")
    parser.add_argument("--source", choices=["ja", "en", "zh"], required=True)
    parser.add_argument("--target", choices=["ja", "en", "zh"], required=True)
    parser.add_argument(
        "--mode",
        choices=["short", "technical", "conversation"],
        default="short",
        help="翻訳モード（short / technical / conversation）",
    )
    parser.add_argument("--conversation-id", default="default")
    parser.add_argument("--relationship", default="")
    parser.add_argument("--speaker", default="")
    parser.add_argument("--history-file", default="data/history.json")
    parser.add_argument("--max-history", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    history = JsonHistoryStore(Path(args.history_file), args.max_history)
    previous_entries = history.list_entries(args.conversation_id)
    translator = VllmTranslator()
    translated_text = translator.translate(
        args.text,
        args.source,
        args.target,
        args.mode,
        history=previous_entries if args.mode == "conversation" else None,
        relationship=args.relationship,
        speaker=args.speaker,
    )

    history.add(
        TranslationEntry(
            source_text=args.text,
            translated_text=translated_text,
            source_lang=args.source,
            target_lang=args.target,
            mode=args.mode,
            conversation_id=args.conversation_id,
            relationship=args.relationship,
            speaker=args.speaker,
        )
    )
    print(translated_text)


if __name__ == "__main__":
    main()
