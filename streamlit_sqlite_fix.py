"""
Streamlit用のSQLite修正スクリプト
このスクリプトは、Streamlitアプリが起動する前に実行し、
システムのSQLiteをpysqlite3に置き換えます
"""

import sys
import importlib.util

# pysqlite3がインストールされているか確認
try:
    import pysqlite3
    # SQLite3をpysqlite3で上書き
    sys.modules["sqlite3"] = pysqlite3
    print("Successfully patched sqlite3 with pysqlite3")
except ImportError:
    print("pysqlite3 not found, using system sqlite3")
    import sqlite3
    print(f"Using sqlite3 version: {sqlite3.sqlite_version}")

# このスクリプトが直接実行された場合は何もしない
if __name__ == "__main__":
    print("This script should be imported, not run directly") 