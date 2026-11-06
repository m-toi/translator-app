"""vLLMのOpenAI互換APIを呼び出す。"""

from dataclasses import dataclass

from .models import TranslationEntry, TranslationMode
from .prompts import build_context, build_messages


@dataclass
class VllmTranslator:
    """localhostで動くvLLMサーバーへの翻訳クライアント。"""

    model: str = "plamo-3-translate"
    base_url: str = "http://localhost:8000/v1"
    api_key: str = "not-needed"
    max_tokens: int = 512

    def translate(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        mode: TranslationMode,
        history: list[TranslationEntry] | None = None,
        relationship: str = "",
        speaker: str = "",
    ) -> str:
        try:
            from openai import OpenAI, OpenAIError
        except ImportError as error:
            raise RuntimeError(
                "openaiが見つかりません。`uv sync`を実行してください。"
            ) from error

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=build_messages(
                    source_text,
                    source_lang,
                    target_lang,
                    mode,
                    history,
                    relationship,
                    speaker,
                ),
                extra_body={
                    "chat_template_kwargs": {
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "context": build_context(mode, relationship, speaker),
                    },
                },
                temperature=0,
                max_tokens=self.max_tokens,
                stop=["<|plamo:tag|>", "<|plamo:bos|>"],
            )
        except OpenAIError as error:
            raise RuntimeError(f"vLLMへの接続または翻訳要求に失敗しました: {error}") from error
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("vLLMから翻訳結果が返されませんでした")
        return content.strip()
