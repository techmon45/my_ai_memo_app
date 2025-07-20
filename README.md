# 🤖 AI Memo App

AIを活用したメモ帳アプリケーションです。メモの作成時に自動的に要約とタグを生成し、効率的なメモ管理を実現します。

## ✨ 機能

- 📝 **メモの作成・編集・削除**
- 🤖 **AI自動要約**: メモの内容を自動的に要約
- 🏷️ **AI自動タグ付け**: 内容に基づいて関連タグを自動生成
- 🔍 **検索機能**: タイトル、内容、タグでの検索
- 📱 **MCP対応**: Model Context Protocolを使用したAI連携

## 🛠️ 技術スタック

- **Backend**: Python, FastMCP, FastAPI
- **Frontend**: Streamlit (予定)
- **AI**: OpenAI GPT-4o-mini
- **Database**: SQLite (予定)
- **Package Manager**: UV
- **Environment**: venv

## 🚀 セットアップ

### 1. UVのインストール

```bash
# UVのインストール（まだインストールしていない場合）
pip install uv
```

### 2. 環境の準備

```bash
# 仮想環境の作成とアクティベート
uv venv

# 依存関係のインストール
uv sync
```

### 3. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# OpenAI APIキーを設定
# .envファイルを編集してOPENAI_API_KEYを設定
```

### 4. MCPサーバーの起動

```bash
python server.py
```

## 📁 プロジェクト構造

```
my_ai_memo_app/
├── src/
│   ├── backend/          # バックエンド関連
│   ├── frontend/         # フロントエンド関連
│   ├── models/           # データモデル
│   │   └── memo.py
│   └── utils/            # ユーティリティ
│       └── ai_processor.py
├── .cursor/              # Cursor設定
├── server.py             # MCPサーバー
├── pyproject.toml        # プロジェクト設定と依存関係
├── .env.example         # 環境変数テンプレート
└── README.md
```

## 🔧 使用方法

### MCPツール

以下のMCPツールが利用可能です：

- `create_memo(title, content, tags)`: 新しいメモを作成
- `get_memo(memo_id)`: メモを取得
- `list_memos()`: すべてのメモをリスト表示
- `update_memo(memo_id, title, content, tags)`: メモを更新
- `delete_memo(memo_id)`: メモを削除
- `search_memos(query)`: メモを検索

### 例

```python
# メモの作成
result = create_memo(
    title="会議メモ",
    content="今日の会議では新しいプロジェクトについて話し合いました。来月から開発を開始予定です。",
    tags=["会議", "プロジェクト"]
)

# メモの検索
results = search_memos("プロジェクト")
```

## 🛠️ 開発コマンド

```bash
# 依存関係のインストール
uv sync

# 開発用依存関係も含めてインストール
uv sync --extra dev

# 新しい依存関係を追加
uv add package-name

# 開発用依存関係を追加
uv add --dev package-name

# 仮想環境でスクリプトを実行
uv run python server.py
```

## 🎯 次のステップ

1. **Web UIの実装**: Streamlitを使用したフロントエンド
2. **データベース統合**: SQLiteを使用した永続化
3. **認証機能**: ユーザー管理システム
4. **高度な検索**: 全文検索エンジンの統合
5. **エクスポート機能**: PDF、Markdown形式でのエクスポート

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

## 📄 ライセンス

MIT License 