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
    def __init__(self, persist_directory="./chromadb_server"):
        """Initialize the vector store with persistent storage."""
        self.persistent_client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "collection_name_server"
        self.collection = self._get_or_create_collection()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

    def _get_or_create_collection(self):
        """Get existing collection or create a new one."""
        try:
            return self.persistent_client.get_collection(name=self.collection_name)
        except:
            return self.persistent_client.create_collection(name=self.collection_name)

    def add_documents(self, documents, ids=None):
        """Add documents to the collection."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Generate embeddings
        embeddings = self.embeddings.embed_documents(documents)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids
        )
        return ids

    def update_documents(self, documents, ids):
        """Update existing documents in the collection."""
        embeddings = self.embeddings.embed_documents(documents)
        self.collection.update(
            documents=documents,
            embeddings=embeddings,
            ids=ids
        )

    def upsert_documents(self, documents, ids):
        """Upsert documents (update if exists, insert if not)."""
        embeddings = self.embeddings.embed_documents(documents)
        self.collection.upsert(
            documents=documents,
            embeddings=embeddings,
            ids=ids
        )

    def delete_documents(self, ids):
        """Delete documents from the collection."""
        self.collection.delete(ids=ids)

    def get_documents(self, ids=None):
        """Get documents from the collection."""
        if ids is None:
            return self.collection.get()
        return self.collection.get(ids=ids)

    def peek(self):
        """Peek at the first 10 items in the collection."""
        return self.collection.peek()

    def search(self, query, n_results=5):
        """Search for similar documents."""
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

    def count(self):
        """Get the number of documents in the collection."""
        return self.collection.count() 