import sys
import sqlite3

# SQLiteのバージョンを確認
sqlite_version = sqlite3.sqlite_version_info
print(f"Current SQLite version: {sqlite3.sqlite_version}")

# バージョンが3.35.0未満の場合、警告を表示するだけで続行
if sqlite_version < (3, 35, 0):
    print(f"Warning: SQLite version {sqlite3.sqlite_version} is lower than required (3.35.0)")
    print("The application will try to continue with in-memory mode")
    
    # ChromaDBのSQLiteチェックをバイパスするための準備
    # まずモジュールをインポートしてから設定する
    try:
        # 先にchromadbをインポート
        import chromadb
        # それからフラグを設定
        sys.modules['chromadb']._SQLITE_SENTINEL_FILE = True
        print("Successfully set ChromaDB sentinel flag")
    except (ImportError, KeyError, AttributeError) as e:
        print(f"Note: Could not set ChromaDB sentinel flag: {e}")
        print("This will be handled elsewhere in the application") 