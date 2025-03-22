import chromadb
from langchain_openai import OpenAIEmbeddings
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv

# Load environment variables
dir_path = dirname(abspath("__file__"))
dotenv_path = join(dir_path, '../.env')
load_dotenv(dotenv_path, verbose=True)

class VectorStore:
    def __init__(self):
        # ChromaDB クライアントの初期化（インメモリモード）
        self.client = chromadb.Client(
            chromadb.Settings(
                is_persistent=False,
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
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