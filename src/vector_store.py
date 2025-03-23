import os
from dotenv import load_dotenv
import sys
import sqlite3

# 環境変数のロード
load_dotenv()

# SQLiteのバージョン確認
print(f"Using SQLite version: {sqlite3.sqlite_version}")

# chromadbのインポート
import chromadb
from langchain_openai import OpenAIEmbeddings

class VectorStore:
    def __init__(self):
        """ChromaDBのベクトルストアを初期化"""
        try:
            # ChromaDBクライアントの初期化（インメモリモード）
            self.client = chromadb.Client(
                chromadb.Settings(
                    is_persistent=False,
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # コレクションの作成
            try:
                self.collection = self.client.get_collection(name="documents")
                print("Collection 'documents' already exists")
            except Exception:
                print("Creating new collection 'documents'")
                self.collection = self.client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )
                
            # 埋め込みモデルの設定
            self.embeddings = OpenAIEmbeddings()
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            self.collection = None
            self.client = None
            self.embeddings = None
            # エラーを上位で処理するために再送出
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

    def upsert_documents(self, documents, ids=None):
        """ドキュメントを追加または更新"""
        try:
            if self.collection is None:
                print("Collection is not available")
                return
            
            # Documentオブジェクトの場合とプレーンテキストの場合の両方に対応
            if hasattr(documents[0], 'page_content'):
                # Documentオブジェクトの場合
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]
            else:
                # プレーンテキストの場合
                texts = documents
                metadatas = [{} for _ in documents]
            
            # IDsの生成または使用
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            # 埋め込みの生成と追加
            embeddings = self.embeddings.embed_documents(texts)
            self.collection.upsert(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Successfully upserted {len(texts)} documents")
        except Exception as e:
            print(f"Error in upsert_documents: {e}")

    def delete_documents(self, ids):
        """ドキュメントを削除"""
        self.collection.delete(ids=ids)

    def get_documents(self, ids=None):
        """ドキュメントを取得"""
        try:
            if self.collection is None:
                return {"ids": [], "documents": [], "metadatas": []}
            
            # idsが指定されていない場合はすべてのドキュメントを取得
            if ids is None:
                return self.collection.get()
            return self.collection.get(ids=ids)
        except Exception as e:
            print(f"Error getting documents: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

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