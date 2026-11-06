"""入力文から簡体字中国語らしさを簡易判定する。"""

import re

# 日本語でも使われる漢字と区別しやすい、簡体字・中国語で頻出する文字。
SIMPLIFIED_CHINESE_HINTS = set(
    "你好吗的了是我他她们这那不在有会对说来个为与也就还没过中"
)


def looks_like_simplified_chinese(text: str) -> bool:
    """外部サービスを使わず、短文向けに中国語らしさを判定する。"""
    cjk_chars = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text)
    if len(cjk_chars) < 2:
        return False

    simplified_hint_count = sum(
        character in SIMPLIFIED_CHINESE_HINTS for character in cjk_chars
    )
    has_japanese_kana = bool(re.search(r"[\u3040-\u30ff]", text))
    if simplified_hint_count >= 1 and not has_japanese_kana:
        return True

    # 簡体字特有語がない場合でも、漢字だけの長めの入力は中国語候補とする。
    return len(cjk_chars) >= 4 and not has_japanese_kana
