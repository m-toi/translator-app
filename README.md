# ローカル翻訳アプリ

PLaMo 3 Translate 8B W4A16を、NVIDIA GPU上のvLLMから呼び出す個人用翻訳アプリです。
現在は、まず動作確認しやすいCLI版を実装しています。
同じバックエンドを使うStreamlit画面も利用できます。

初回セットアップからvLLM起動までの手順は
[SETUP.md](SETUP.md) を参照してください。

## 起動と停止を自動化する

2つのターミナルを手動で開く代わりに、1つのターミナルで次を実行できます。

```bash
cd ~/projects/translate_app
bash scripts/start.sh
```

vLLMとStreamlitがバックグラウンドで起動します。ブラウザで
`http://localhost:8501` を開いてください。

状態確認と停止は次のコマンドです。

```bash
bash scripts/status.sh
bash scripts/stop.sh
```

ログは `logs/vllm.log` と `logs/streamlit.log` に保存されます。

Streamlit画面では、文章を改行したとき、または「翻訳する」ボタンを押したときだけ
翻訳と履歴保存が行われます。改行すると各行が別々の翻訳履歴として保存されます。
「翻訳する」ボタンでは入力内容を明示的に再翻訳できます。
会話モードでは入力欄の上にある「自分／相手」スイッチで発言者を選択します。
原文と翻訳先の言語は入力欄の上で設定でき、中央の`⇄`ボタンでワンクリック交換できます。

## 対応モード

- `short`: 短文を簡潔に翻訳
- `technical`: コード、関数名、変数名、パスなどを保持して翻訳
- `conversation`: 関係性、話者、同じ会話の履歴を考慮して翻訳

## 環境構築

Pythonのバージョンと依存関係はuvで管理します。

```bash
uv sync --dev
```

`.python-version` はvLLMの互換性を考慮してPython 3.13を指定しています。

## vLLMサーバーの起動

モデルのREADMEに従ってモデルをダウンロードし、モデルディレクトリで次を実行します。
RTX 3060（VRAM 12GB）では、まずモデルREADMEの16,384トークン設定を試し、
GPUメモリ不足の場合は `--max-model-len` を小さくしてください。

```bash
uv run --with vllm --with huggingface-hub hf download \
  pfnet/plamo-3-translate-8b-W4A16 \
  --local-dir plamo-3-translate-8b-W4A16
cd plamo-3-translate-8b-W4A16
uv run --with vllm --with openai --with numba vllm serve . \
  --trust-remote-code \
  --served-model-name plamo-3-translate \
  --max-model-len 16384 \
  --max-num-seqs 4 \
  --dtype bfloat16
```

vLLMのGPU依存関係は環境によって異なるため、上記で失敗する場合は
[plamo3_README.md](plamo3_README.md) のvLLM手順を確認してください。

## CLIの実行

別のターミナルでプロジェクトのルートから実行します。

```bash
uv run python main.py "こんにちは。" --source ja --target en
uv run python main.py "Deploy the API." --source en --target ja --mode technical
uv run python main.py "明日の予定は大丈夫？" --source ja --target en \
  --mode conversation \
  --conversation-id friend \
  --relationship "親しい友人" \
  --speaker "自分"
```

翻訳履歴は `data/history.json` に保存されます。初期値では最新100件だけを保存し、
上限を超えると古い履歴から削除します。

```bash
uv run python main.py "保存件数を変える" --source ja --target en --max-history 50
```

## Streamlit画面の実行

```bash
uv run streamlit run app.py
```

ブラウザで画面が開いたら、原文・言語・モードを選んで翻訳します。
会話モードでは、会話IDが同じ履歴だけが文脈として使われます。

## テスト

vLLMサーバーを起動しなくても、履歴のFIFO削除などをテストできます。

```bash
uv run python -m pytest
```
