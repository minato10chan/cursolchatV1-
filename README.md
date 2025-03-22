# Ask the Doc App

ドキュメントに対して質問できるAIアプリケーションです。

## セットアップ方法

1. リポジトリをクローン
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. 必要なパッケージをインストール
```bash
pip install -r requirements.txt
```

3. 環境変数の設定
- `.env.example`ファイルを`.env`にコピー
```bash
cp .env.example .env
```
- `.env`ファイルを開き、必要なAPIキーを設定
  - `OPENAI_API_KEY`: OpenAI APIキー
  - その他のAPIキー（必要な場合）

## 使用方法

1. アプリケーションの起動
```bash
streamlit run app.py
```

2. ブラウザで`http://localhost:8501`にアクセス

3. ドキュメントのアップロードと質問
- 「ChromaDB 管理」ページでドキュメントをアップロード
- 「質問する」ページでドキュメントについて質問

## 注意事項

- APIキーは`.env`ファイルで管理され、GitHubにはアップロードされません
- `.env`ファイルは必ず`.gitignore`に含まれており、誤ってコミットされないようになっています
- 本番環境では、適切なセキュリティ対策を行ってください

## ライセンス

MIT License 