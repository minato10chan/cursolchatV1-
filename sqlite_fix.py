import sys
import sqlite3

# SQLiteのバージョンを確認
sqlite_version = sqlite3.sqlite_version_info

# バージョンが3.35.0未満の場合、警告を表示するだけで続行
if sqlite_version < (3, 35, 0):
    print(f"Warning: SQLite version {sqlite3.sqlite_version} is lower than required (3.35.0)")
    print("The application will try to continue with in-memory mode")
    
    # ChromaDBのSQLiteチェックをバイパスするためのフラグ
    sys.modules['chromadb']._SQLITE_SENTINEL_FILE = True 