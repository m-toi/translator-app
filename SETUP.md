# ローカル翻訳システム セットアップ手順

この文書は、現在の `translate_app` を初めて使える状態にするための手順です。

## 1. 想定環境

- WSL2 Ubuntu
- CPU: AMD Ryzen 5 3600
- GPU: NVIDIA GeForce RTX 3060（VRAM 12GB）
- メモリ: 48GB
- Python: 3.13
- 推論サーバー: vLLM
- モデル: `pfnet/plamo-3-translate-8b-W4A16`

このアプリは、ローカルで起動したvLLMサーバーへ接続して翻訳します。
翻訳時に外部の翻訳APIは使用しません。

## 2. Windows側の準備

### NVIDIAドライバー

Windows側に、WSL2でGPUを利用できるNVIDIAドライバーをインストールします。
インストール後、Windowsを再起動してください。

WSL UbuntuでGPUが認識されることを確認します。

```bash
nvidia-smi
```

RTX 3060の情報が表示されれば、GPUの準備は完了です。
`nvidia-smi: command not found` になる場合は、Windows側のNVIDIAドライバーやWSL2の設定を確認してください。

## 3. uvのインストール

WSL Ubuntuで実行します。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

`uv` のバージョンが表示されれば完了です。
新しいターミナルを開いた場合に `uv` が見つからなければ、もう一度次を実行します。

```bash
source "$HOME/.local/bin/env"
```

## 4. プロジェクトの依存関係を準備

既存のプロジェクトディレクトリへ移動します。

```bash
cd ~/projects/translate_app
uv sync --dev
```

このコマンドで、次のものが準備されます。

- Python 3.13の仮想環境 `.venv`
- CLIとvLLM API接続に必要な `openai`
- Web画面に必要な `streamlit`
- テストに必要な `pytest`

インストールできたことを確認します。

```bash
uv run python --version
uv run python -m pytest
```

テストが4件成功すれば、アプリ側の基本準備は完了です。

## 5. 翻訳モデルをダウンロード

モデル本体は大きいため、ディスク容量とネットワーク通信が必要です。
プロジェクトのルートで次を実行します。

```bash
cd ~/projects/translate_app
uv run --with huggingface-hub hf download \
  pfnet/plamo-3-translate-8b-W4A16 \
  --local-dir plamo-3-translate-8b-W4A16
```

完了すると、次のディレクトリが作成されます。

```text
~/projects/translate_app/plamo-3-translate-8b-W4A16
```

## 6. vLLMサーバーを起動

### 初回起動

ターミナルを1つ開いたまま、次を実行します。

```bash
cd ~/projects/translate_app/plamo-3-translate-8b-W4A16

uv run --with vllm --with openai --with numba vllm serve . \
  --trust-remote-code \
  --served-model-name plamo-3-translate \
  --max-model-len 8192 \
  --max-num-seqs 1 \
  --gpu-memory-utilization 0.90 \
  --dtype bfloat16
```

RTX 3060のVRAMは12GBなので、最初は負荷を抑えた設定にしています。
サーバーが起動すると、通常は `http://localhost:8000` で待ち受けます。
このターミナルは、翻訳を使っている間は閉じないでください。

### GPUメモリ不足になった場合

`CUDA out of memory` などが表示された場合は、サーバーを停止してから
`--max-model-len` を小さくして再起動します。

```bash
uv run --with vllm --with openai --with numba vllm serve . \
  --trust-remote-code \
  --served-model-name plamo-3-translate \
  --max-model-len 4096 \
  --max-num-seqs 1 \
  --gpu-memory-utilization 0.85 \
  --dtype bfloat16
```

### `nvcc` が見つからない場合

`error.txt` の今回の原因はGPUメモリ不足ではなく、次のエラーです。

```text
RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist
```

vLLMがFlashInferのサンプラーを起動時にJITコンパイルしようとしましたが、
WSL内にCUDA Toolkit（`nvcc`）がないため失敗しています。FlashInferの警告にある
「FlashInfer kernels are disabled」は単独では致命的ではなく、後からサンプラーが
FlashInferを選んで失敗していることが本当の原因です。

まずはFlashInferのサンプラーを無効にして起動してください。
CUDA Toolkitを追加インストールしなくても試せます。

```bash
cd ~/projects/translate_app/plamo-3-translate-8b-W4A16

VLLM_USE_FLASHINFER_SAMPLER=0 \
uv run --with vllm --with openai --with numba vllm serve . \
  --trust-remote-code \
  --served-model-name plamo-3-translate \
  --max-model-len 4096 \
  --max-num-seqs 1 \
  --gpu-memory-utilization 0.85 \
  --dtype bfloat16 \
  --enforce-eager
```

この設定ではFlashInfer以外のサンプラーへ切り替わるため、速度やメモリ使用量が
変わる可能性があります。まず起動確認を優先してください。

FlashInferを使いたい場合は、代わりにvLLM対応の事前コンパイル済みカーネルを
取得する方法もあります。

```bash
uv run --with vllm vllm download-kernels
```

それでもJITコンパイルが必要な場合は、WSLにCUDA Toolkitと`nvcc`を導入し、
次を確認します。

```bash
nvcc --version
```

CUDA Toolkitの導入は、Windows側のNVIDIAドライバーとは別です。
まずはサンプラー無効化で動作確認することを推奨します。

### サーバーの動作確認

別のターミナルで実行します。

```bash
curl http://localhost:8000/v1/models
```

レスポンスに `plamo-3-translate` が含まれていれば、vLLMサーバーは利用可能です。

## 7. CLIで翻訳

vLLMサーバーを起動したまま、別のターミナルで実行します。

```bash
cd ~/projects/translate_app
uv run python main.py "こんにちは。" \
  --source ja \
  --target en
```

言語コードは次の3種類に対応しています。

| コード | 言語 |
|---|---|
| `ja` | 日本語 |
| `en` | 英語 |
| `zh` | 中国語（簡体字） |

### 技術翻訳

```bash
uv run python main.py \
  'Call my_function() from /app/config.py.' \
  --source en \
  --target ja \
  --mode technical
```

技術翻訳では、関数名、変数名、パス、URL、API名、コマンドなどを
翻訳しないように指示します。

### 会話翻訳

```bash
uv run python main.py "明日の予定は大丈夫？" \
  --source ja \
  --target en \
  --mode conversation \
  --conversation-id friend \
  --relationship "親しい友人" \
  --speaker "自分"
```

同じ `--conversation-id` を指定した履歴が、次の会話翻訳の文脈として使われます。

## 8. Streamlit画面を使う

vLLMサーバーを起動したまま、別のターミナルで実行します。

```bash
cd ~/projects/translate_app
uv run streamlit run app.py
```

表示されたURL（通常は `http://localhost:8501`）をブラウザで開きます。

画面では次を設定できます。

- 原文の言語
- 翻訳先の言語
- 短文・技術・会話モード
- 会話ID
- 相手との関係
- 話者
- 保存する最大やり取り数

## 9. 履歴ファイル

翻訳履歴は次のファイルに保存されます。

```text
~/projects/translate_app/data/history.json
```

初期値では最新100件だけを保存します。
上限を超えると、新しい翻訳を保存するタイミングで古い履歴から削除します。

保存件数を変更する場合は、CLIでは次のように指定します。

```bash
uv run python main.py "テスト" \
  --source ja \
  --target en \
  --max-history 50
```

履歴を削除したい場合は、vLLMとStreamlitを停止してから次を実行します。

```bash
rm -f data/history.json
```

## 10. よくある問題

### `uv: command not found`

uvのパスを読み込みます。

```bash
source "$HOME/.local/bin/env"
```

### `nvidia-smi` が失敗する

Windows側のNVIDIAドライバーがWSL2に対応しているか確認します。
WSL内にLinux用NVIDIAドライバーを重ねてインストールするのではなく、
基本的にはWindows側のドライバーを更新します。

### `Connection refused` が表示される

vLLMサーバーが起動していないか、起動途中の可能性があります。
先に `/v1/models` を確認してください。

```bash
curl http://localhost:8000/v1/models
```

### `CUDA out of memory` が表示される

vLLMを停止し、次の順で設定を小さくします。

1. `--max-model-len 8192` を `4096` に変更
2. `--max-num-seqs 1` を維持
3. `--gpu-memory-utilization 0.90` を `0.85` に変更
4. 他のGPU使用中プロセスを終了

### 履歴ファイルが壊れている

アプリは成功したように見せず、履歴読み込みエラーを表示します。
必要な履歴を退避してから削除し、再作成してください。

```bash
mv data/history.json data/history.json.backup
```

## 11. 停止方法

vLLMまたはStreamlitを実行しているターミナルで、次を押します。

```text
Ctrl+C
```

vLLMを停止しても、モデルファイルと履歴ファイルは削除されません。

## 12. 起動と停止を自動化

毎回2つのターミナルを開く代わりに、プロジェクトのルートで次を実行します。

```bash
cd ~/projects/translate_app
bash scripts/start.sh
```

vLLMとStreamlitがバックグラウンドで起動し、ターミナルを閉じても動作します。
vLLMの準備が完了してから、ブラウザで`http://localhost:8501`を開いてください。

状態確認：

```bash
bash scripts/status.sh
```

停止：

```bash
bash scripts/stop.sh
```

ログ確認：

```bash
tail -f logs/vllm.log
tail -f logs/streamlit.log
```

起動に失敗した場合は、ログの先頭または末尾にある最初のエラーを確認してください。

### 入力と同時に翻訳する

Streamlit画面の入力欄では、入力内容の変更が確定すると自動的に翻訳されます。
「もう一度翻訳する」ボタンを押せば、同じ内容も再翻訳できます。

入力を改行すると、空行を除く各行がそれぞれ1回のやり取りとして翻訳され、
JSON履歴にも個別に保存されます。会話モードでは、同じ会話IDの過去行が
次の行の文脈として使われます。
会話モードの入力欄の上には「自分／相手」スイッチが表示されます。
入力する発言に合わせて選択すると、選択内容が話者情報として履歴と翻訳文脈に保存されます。

Streamlitは入力中のキー入力1文字ごとではなく、入力欄の変更が画面へ反映された
タイミングで処理します。vLLMへ1文字ごとにリクエストを送らないため、
GPU負荷を抑えられます。

### 中国語DMを貼り付けて翻訳する

中国語（簡体字）の文章を文章欄へ貼り付けると、入力変更時に簡易判定を行い、
原文を中国語、翻訳先を日本語へ自動設定して、そのまま翻訳します。
サイドバーで原文言語や翻訳先を手動変更した場合は、手動設定を優先します。
自動判定を再び使いたい場合は、サイドバーの「言語の自動判定を再開」を押してください。

短すぎる文や日本語と共通する漢字だけの文は、自動判定できない場合があります。
その場合はサイドバーで原文を中国語、翻訳先を日本語に設定してください。

## 12. `chat_template_kwargs` のエラー

次のエラーが出る場合があります。

```text
TypeError: Completions.create() got an unexpected keyword argument 'chat_template_kwargs'
```

これはOpenAI PythonクライアントがvLLM固有の引数を直接受け付けないことが原因です。
現在のアプリは`chat_template_kwargs`を`extra_body`へ入れて送信する実装になっています。
プロジェクトを更新した場合は、次を実行してから再度CLIを起動してください。

```bash
cd ~/projects/translate_app
uv sync
uv run python main.py "こんにちは。" --source ja --target en
```
