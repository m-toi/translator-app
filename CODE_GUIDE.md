# translate_app ソースコード入門

この文書は、`translate_app` の各フォルダ・ファイルが何を担当しているかを、
PythonやStreamlitを学び始めた人向けに説明するものです。

## 1. このシステム全体の役割

このシステムは、次の3つを組み合わせて動きます。

1. **vLLM**  
   PLaMo 3 Translate 8B W4A16をGPU上で動かし、翻訳結果を生成します。
2. **Pythonアプリ**  
   入力内容、翻訳モード、会話履歴を整理して、vLLMへリクエストします。
3. **Streamlit**  
   ブラウザに入力欄や設定画面を表示します。

全体の流れは次のとおりです。

```text
ブラウザ
  ↓
app.py
  ↓
line_translation.py
  ↓
translator.py
  ↓
vLLM（localhost:8000）
  ↓
PLaMo 3 Translate
```

翻訳履歴は、vLLMとは別に次のJSONファイルへ保存されます。

```text
data/history.json
```

## 2. フォルダ構成

```text
translate_app/
├── app.py
├── main.py
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── README.md
├── SETUP.md
├── CODE_GUIDE.md
├── plamo3_README.md
├── translate_app/
│   ├── __init__.py
│   ├── models.py
│   ├── history.py
│   ├── prompts.py
│   ├── translator.py
│   ├── line_translation.py
├── tests/
│   ├── test_history.py
│   ├── test_line_translation.py
│   ├── test_prompts.py
└── scripts/
    ├── start.sh
    ├── stop.sh
    └── status.sh
```

次のフォルダ・ファイルは実行後に作成されます。

```text
data/       翻訳履歴
logs/       vLLMとStreamlitのログ
.run/       起動したプロセスのPID
.venv/      uvが作成するPython仮想環境
```

これらのうち、`.venv/`、`data/`、`logs/`、`.run/`は`.gitignore`でGit管理から除外しています。

## 3. ルート直下のファイル

### `app.py`：ブラウザ画面の本体

[app.py](app.py) は、Streamlitで表示する画面を定義しています。
`uv run streamlit run app.py` で実行します。

主な処理は次のとおりです。

- 言語選択欄を表示する
- 入力欄の上に原文・翻訳先の言語と入れ替えボタンを表示する
- 短文・技術・会話モードを選択する
- 会話ID、関係、話者を入力する
- 会話モードの「自分／相手」スイッチを表示する
- 入力欄の上で原文と翻訳先の言語を手動設定する
- 改行またはボタン押下時に翻訳を開始する
- 翻訳結果と会話履歴を表示する

Streamlitは、画面操作のたびにPythonファイル全体を上から再実行します。
そのため、画面をまたいで保持したい値は`st.session_state`へ保存しています。

例えば、次の値は再実行後も保持されます。

```python
st.session_state.last_input
st.session_state.translated_lines
```

翻訳処理の細部は`app.py`にすべて書かず、後述のモジュールへ分けています。
これにより、画面と翻訳ロジックを別々にテストできます。

### `main.py`：コマンドライン版の入口

[main.py](main.py) は、ターミナルから翻訳する場合の入口です。

```bash
uv run python main.py "こんにちは。" --source ja --target en
```

`argparse`でコマンドライン引数を読み取り、次の処理を行います。

1. 指定された引数を読み込む
2. 履歴を読み込む
3. `VllmTranslator`で翻訳する
4. `TranslationEntry`を作る
5. JSON履歴へ保存する
6. 翻訳結果を表示する

ブラウザを使わずに、バックエンドの翻訳機能を確認したいときに便利です。

### `pyproject.toml`：Pythonプロジェクトの設定

[pyproject.toml](pyproject.toml) には、プロジェクト名、Pythonの対応バージョン、
依存パッケージ、開発用パッケージが書かれています。

主な依存パッケージは次のとおりです。

- `openai`：vLLMのOpenAI互換APIを呼び出す
- `streamlit`：ブラウザ画面を作る
- `pytest`：テストを実行する

依存関係を変更した場合は、次を実行します。

```bash
uv sync --dev
```

### `uv.lock`：依存関係の固定情報

[uv.lock](uv.lock) は、実際にインストールするパッケージのバージョンを固定します。
通常は手で編集せず、`uv add`や`uv sync`に更新させます。

### `.python-version`：Pythonバージョン

[.python-version](.python-version) には、uvが使用するPythonのバージョンが書かれています。
現在はvLLMとの互換性を考慮してPython 3.13を指定しています。

### `.gitignore`：Gitへ保存しないもの

[.gitignore](.gitignore) は、仮想環境、ログ、履歴などをGitの対象外にします。
翻訳履歴には個人情報が含まれる可能性があるため、特に`data/`を管理対象外にしています。

### `README.md`：短い使い方

[README.md](README.md) は、日常的に参照する簡潔な説明書です。
詳細な初回構築手順は[SETUP.md](SETUP.md)に分けています。

### `SETUP.md`：初回構築とトラブル対応

[SETUP.md](SETUP.md) には、次の手順があります。

- NVIDIA GPUの確認
- uvのインストール
- Python依存関係の準備
- モデルのダウンロード
- vLLMの起動
- CLIとStreamlitの起動
- GPUメモリ不足や`nvcc`エラーへの対応
- 起動スクリプトの使い方

### `plamo3_README.md`：モデル公式資料

[plamo3_README.md](plamo3_README.md) は、PLaMoモデルの配布元資料です。
モデルの仕様、対応言語、PFML3形式、vLLMの起動方法などを確認できます。
モデル固有の仕様を変更するときは、まずこの資料を確認します。

### `CODE_GUIDE.md`：この解説書

このファイルです。コードの役割を調べるときの入口として使います。

## 4. `translate_app/`パッケージ

### `__init__.py`

[__init__.py](translate_app/__init__.py) は、`translate_app`をPythonパッケージとして扱うためのファイルです。
現在はパッケージであることを示す役割だけを持っています。

### `models.py`：データの形

[models.py](translate_app/models.py) は、翻訳履歴のデータ構造を定義します。

中心となる`TranslationEntry`は、1回分の翻訳を表します。

```text
原文
翻訳結果
原文の言語
翻訳先の言語
翻訳モード
会話ID
関係
話者
作成日時
```

`to_dict()`はPythonオブジェクトをJSON保存用の辞書へ変換します。
`from_dict()`はJSONの辞書を`TranslationEntry`へ戻します。

また、`LanguageCode`と`TranslationMode`で、使用できる言語コードとモードを表しています。

### `history.py`：履歴の読み書き

[history.py](translate_app/history.py) は、JSON履歴の保存処理を担当します。

`HistoryStore`は、保存先が持つべき操作を示すプロトコルです。

```text
list_entries()：履歴を読む
add()：履歴を追加する
```

現在の実装は`JsonHistoryStore`です。
将来SQLiteへ移行するときは、SQLite版のクラスを追加して同じ操作を実装すれば、
画面や翻訳処理を大きく変更せずに済みます。

履歴を追加するときは、次の順で処理します。

1. JSONを読む
2. 新しい履歴を末尾へ追加する
3. 最大件数を超えた古い履歴を削除する
4. 一時ファイルへ書き込む
5. `os.replace()`で本来のファイルへ置き換える

途中でアプリが終了しても壊れにくいように、一時ファイルを使っています。

### `prompts.py`：PLaMoへの指示を作る

[prompts.py](translate_app/prompts.py) は、翻訳モードごとの指示と会話履歴の形を作ります。

`MODE_INSTRUCTIONS`には、次の指示があります。

- `short`：翻訳結果だけを返す
- `technical`：コードや関数名などを保持する
- `conversation`：関係や会話履歴を考慮する

PLaMoは会話履歴を`user`と`assistant`の組み合わせで受け取るため、
`build_messages()`が過去の原文と翻訳を次の形へ変換します。

```text
user      過去の原文
assistant 過去の翻訳
user      今回の原文
```

`build_context()`は、翻訳モード、相手との関係、話者をPLaMoの`context`へまとめます。

### `translator.py`：vLLMへ翻訳を依頼する

[translator.py](translate_app/translator.py) の`VllmTranslator`は、vLLMのAPIクライアントです。

vLLMはOpenAI互換APIを提供しているため、`openai`パッケージを使って呼び出します。

```text
http://localhost:8000/v1
```

`translate()`は次の値を送ります。

- モデル名
- user/assistant形式の会話メッセージ
- 原文言語
- 翻訳先言語
- 翻訳モードの文脈
- 温度`0`
- 最大出力トークン数
- PLaMo用の停止文字列

PLaMo固有の`chat_template_kwargs`は、OpenAIクライアントの型にないため、
`extra_body`へ入れてvLLMへ渡しています。

APIエラーは`RuntimeError`へ変換し、画面やCLIでエラーとして表示できるようにしています。

### `line_translation.py`：改行単位の翻訳

[line_translation.py](translate_app/line_translation.py) の`translate_lines()`は、
Streamlitの入力欄を改行で分割します。

```text
1行目 → 1回の翻訳
2行目 → 1回の翻訳
空行  → 無視
```

翻訳結果は`LineTranslation`として画面表示用にまとめます。
同じ入力を何度も翻訳しないよう、言語・モード・会話IDなどを含むキャッシュキーを使います。

会話モードでは、各行を履歴へ保存した後、次の行の履歴として読み込むため、
同じ入力欄内の前の行も後の行の文脈になります。

## 5. `tests/`フォルダ

テストは、vLLMを起動しなくても実行できるように作っています。

### `test_history.py`

[test_history.py](tests/test_history.py) は、次を確認します。

- 最大件数を超えたら古い履歴が削除される
- 会話IDで履歴を絞り込める

### `test_line_translation.py`

[test_line_translation.py](tests/test_line_translation.py) は、次を確認します。

- 改行で分割される
- 空行が無視される
- 各行が履歴へ保存される
- 履歴を個別にJSONから削除できる
- 翻訳済みの行がキャッシュから再利用される
- 翻訳先が変わったらキャッシュを再利用しない

### `test_prompts.py`

[test_prompts.py](tests/test_prompts.py) は、次を確認します。

- 技術翻訳のメッセージが作られる
- 会話履歴がuser/assistantの組になる
- 関係や話者を含む文脈が作られる

すべてのテストを実行するコマンドは次のとおりです。

```bash
uv run python -m pytest
```

## 6. `scripts/`フォルダ

### `start.sh`

[start.sh](scripts/start.sh) は、vLLMとStreamlitをバックグラウンドで起動します。

- vLLMをポート8000で起動する
- Streamlitをポート8501で起動する
- プロセスIDを`.run/`へ保存する
- 出力を`logs/`へ保存する
- FlashInferサンプラーを無効にする

### `stop.sh`

[stop.sh](scripts/stop.sh) は、`start.sh`で起動したプロセスをPIDから停止します。
vLLMとStreamlitをまとめて終了できます。

### `status.sh`

[status.sh](scripts/status.sh) は、PIDファイルとプロセスの存在を確認し、
各サービスが起動中か停止中かを表示します。

まとめて操作するには、次を使います。

```bash
bash scripts/start.sh
bash scripts/status.sh
bash scripts/stop.sh
```

## 7. 1回の翻訳で何が起こるか

### ブラウザから入力する場合

1. `app.py`が入力欄の内容を受け取る
2. 手動設定された言語を使う
3. 改行追加またはボタン押下を翻訳トリガーとして判定する
4. `line_translation.py`が文章を行へ分ける
5. `history.py`から同じ会話の履歴を読む
6. `prompts.py`がメッセージと文脈を作る
7. `translator.py`がvLLMへ送る
8. vLLMがPLaMoで翻訳する
9. 翻訳成功と同時にJSON履歴へ保存する
10. 会話モードでは保存済み履歴を次回翻訳の文脈として表示する
11. 履歴の削除操作があればJSONから削除する
12. Streamlitが結果をブラウザへ表示する

### CLIから入力する場合

1. `main.py`がコマンドライン引数を読む
2. `history.py`から履歴を読む
3. `translator.py`がvLLMへ送る
4. `models.py`で履歴データを作る
5. `history.py`へ保存する
6. 翻訳結果をターミナルへ表示する

## 8. 初学者が変更しやすい場所

### 翻訳モードの指示を変える

[prompts.py](translate_app/prompts.py) の`MODE_INSTRUCTIONS`を変更します。
例えば技術翻訳で保持したい対象を追加できます。

### 保存件数を変える

画面の「保存する最大やり取り数」またはCLIの`--max-history`を変更します。
保存処理自体は[history.py](translate_app/history.py)にあります。

### vLLMの接続先を変える

[translator.py](translate_app/translator.py) の`base_url`を変更します。
ただし、個人利用で外部へ送信したくない場合はlocalhostのままにします。

### 履歴保存をSQLiteへ移行する

[history.py](translate_app/history.py) の`HistoryStore`と同じ
`list_entries()`、`add()`を持つSQLiteクラスを追加します。
画面側が`JsonHistoryStore`ではなくSQLiteクラスを使うように差し替えれば、
翻訳処理やUIの大部分を再利用できます。

## 9. 変更後の確認

Pythonコードを変更したら、次を実行します。

```bash
cd ~/projects/translate_app
uv run python -m pytest
uv run python -m compileall -q translate_app app.py main.py
```

Streamlitの画面変更も確認する場合は、次を実行します。

```bash
uv run streamlit run app.py
```

テストが成功していても、実際の翻訳にはvLLMサーバーが起動している必要があります。
画面が翻訳できない場合は、まず次を確認します。

```bash
curl http://localhost:8000/v1/models
```

`plamo-3-translate`が表示されれば、vLLMはAPIを受け付けられる状態です。
