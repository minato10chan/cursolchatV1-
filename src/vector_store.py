import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv
import sys
import sqlite3

# Load environment variables
load_dotenv()

# SQLiteバージョンを確認して警告
sqlite_version = sqlite3.sqlite_version
print(f"Vector store using SQLite version: {sqlite_version}")

# ChromaDBのSQLiteバージョンチェックをバイパスする試み
# バージョンが3.35.0未満の場合はDuckDBを使用
USE_DUCKDB = False
if sqlite3.sqlite_version_info < (3, 35, 0):
    print("SQLite version is lower than required. Using DuckDB instead.")
    USE_DUCKDB = True
    
    # ChromaDBをインポートする前に設定を環境変数で行う
    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    
    # センチネルファイルを設定
    try:
        # 実際のchromadbライブラリをインポート
        import chromadb
        # センチネルファイルフラグを設定
        if hasattr(chromadb, "_SQLITE_SENTINEL_FILE"):
            chromadb._SQLITE_SENTINEL_FILE = True
        else:
            print("Warning: Could not set _SQLITE_SENTINEL_FILE attribute")
    except Exception as e:
        print(f"Error preparing ChromaDB: {e}")

# 修正の後でchromadbをインポート
import chromadb
from langchain_openai import OpenAIEmbeddings

class VectorStore:
    def __init__(self):
        try:
            # ChromaDB クライアントの初期化（インメモリモード）
            settings = {}
            
            # DuckDB+Parquetを使用する場合
            if USE_DUCKDB:
                settings = chromadb.Settings(
                    chroma_db_impl="duckdb+parquet",  # SQLiteではなくDuckDBを使用
                    persist_directory=None,  # インメモリモード
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            # SQLiteを使用する場合
            else:
                settings = chromadb.Settings(
                    is_persistent=False,  # インメモリモード
                    anonymized_telemetry=False,
                    allow_reset=True
                )
                
            print(f"Initializing ChromaDB with settings: {settings}")
            self.client = chromadb.Client(settings)
            
            # コレクションの作成または取得
            try:
                # まず既存のコレクションを取得
                self.collection = self.client.get_collection(name="documents")
                print("Collection 'documents' already exists, using existing collection")
            except Exception as e:
                print(f"Collection not found, creating new: {e}")
                # 存在しない場合は新しく作成
                self.collection = self.client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )
                print("Created new collection 'documents'")
                
            # 埋め込みモデルの設定
            self.embeddings = OpenAIEmbeddings()
            
        except Exception as e:
            print(f"Critical error initializing ChromaDB: {e}")
            # ダミーコレクションとしてフォールバック
            self.collection = None
            self.client = None
            self.embeddings = None
            # エラーを再送出して上位で処理
            raise

    def add_documents(self, documents):
        """ドキュメントを追加"""
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        embeddings = self.embeddings.embed_documents(texts)
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def update_documents(self, documents):
        """ドキュメントを更新"""
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        embeddings = self.embeddings.embed_documents(texts)
        self.collection.update(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def upsert_documents(self, documents):
        """ドキュメントを追加または更新"""
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        embeddings = self.embeddings.embed_documents(texts)
        self.collection.upsert(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def delete_documents(self, ids):
        """ドキュメントを削除"""
        self.collection.delete(ids=ids)

    def get_documents(self, ids):
        """ドキュメントを取得"""
        return self.collection.get(ids=ids)

    def search(self, query, n_results=5):
        """クエリに基づいてドキュメントを検索"""
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

    def count(self):
        """ドキュメント数を取得"""
        return self.collection.count() 