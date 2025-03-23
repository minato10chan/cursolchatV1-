import chromadb
from langchain_openai import OpenAIEmbeddings
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# ChromaDBのSQLiteバージョンチェックをバイパスするための試み
try:
    import chromadb
    # ChromaDBのインポート成功後にフラグを設定
    sys.modules['chromadb']._SQLITE_SENTINEL_FILE = True
except (ImportError, AttributeError) as e:
    print(f"Error setting up ChromaDB: {e}")

class VectorStore:
    def __init__(self):
        # ChromaDB クライアントの初期化（インメモリモード）
        try:
            self.client = chromadb.Client(
                chromadb.Settings(
                    chroma_db_impl="duckdb+parquet",  # SQLiteではなくDuckDBを使用
                    persist_directory=None,  # インメモリモード
                    is_persistent=False,
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # コレクションの作成または取得
            try:
                self.collection = self.client.get_collection(name="documents")
                print("Collection 'documents' already exists, using existing collection")
            except Exception:
                print("Creating new collection 'documents'")
                self.collection = self.client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            # フォールバックとして空のコレクションを作成
            from chromadb.api.models.Collection import Collection
            self.collection = None
            
        # 埋め込みモデルの設定
        self.embeddings = OpenAIEmbeddings()

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