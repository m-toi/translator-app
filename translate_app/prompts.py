"""PLaMo 3 Translate用の入力メッセージを組み立てる。"""

from .models import TranslationEntry, TranslationMode

MODE_INSTRUCTIONS: dict[TranslationMode, str] = {
    "short": "短い翻訳です。説明や注釈を付けず、翻訳結果だけを返してください。",
    "technical": (
        "技術翻訳です。コードブロック、関数名、変数名、クラス名、"
        "ファイルパス、URL、API名、コマンドは翻訳せず、そのまま保持してください。"
        "説明や注釈を付けず、翻訳結果だけを返してください。"
    ),
    "conversation": (
        "会話の翻訳です。話者との関係、会話履歴、丁寧さを考慮し、"
        "自然な訳にしてください。説明は付けず、翻訳結果だけを返してください。"
    ),
}


def build_messages(
    source_text: str,
    source_lang: str,
    target_lang: str,
    mode: TranslationMode,
    history: list[TranslationEntry] | None = None,
    relationship: str = "",
    speaker: str = "",
) -> list[dict[str, str]]:
    """vLLMのChat Completions APIへ渡すメッセージを作る。"""
    messages: list[dict[str, str]] = []
    for entry in history or []:
        # PLaMoはsystemメッセージではなく、user/assistantの対で履歴を受け取る。
        messages.extend(
            [
                {"role": "user", "content": entry.source_text},
                {"role": "assistant", "content": entry.translated_text},
            ]
        )
    messages.append({"role": "user", "content": source_text})
    return messages


def build_context(
    mode: TranslationMode,
    relationship: str = "",
    speaker: str = "",
) -> str:
    """PLaMoのcontextオプションに渡す補足情報を作る。"""
    context_lines = [MODE_INSTRUCTIONS[mode]]
    if relationship:
        context_lines.append(f"相手との関係: {relationship}")
    if speaker:
        context_lines.append(f"今回の話者: {speaker}")
    return "\n".join(context_lines)
