import chromadb
from chromadb.config import Settings
import json
import yaml
import os
import threading
import time

os.environ["CHROMADB_SQLITE_JOURNAL_MODE"] = "WAL"
os.environ["CHROMADB_SQLITE_TIMEOUT"] = "30"

class ChromaManager:
    def __init__(self, db_path):
        # Clear system cache before initializing client.
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        self.client = chromadb.Client(Settings(persist_directory=db_path))
        self.collections = {}
        # Create a lock to serialize database write operations.
        self.db_lock = threading.Lock()

    def get_or_create_collection(self, collection_name):
        if collection_name not in self.collections:
            # Optionally, you could wrap get_or_create_collection too if needed.
            self.collections[collection_name] = self.client.get_or_create_collection(collection_name)
        return self.collections[collection_name]

    def add_qa(self, collection_name, content, metadata, id=None):
        collection = self.get_or_create_collection(collection_name)
        if id is None:
            id = str(collection.count() + 1)
        # Use lock to prevent concurrent writes.
        with self.db_lock:
            collection.add(
                documents=[json.dumps(content)],
                metadatas=[metadata],
                ids=[id]
            )

    def service_get_qa(self, query, keyword, n_results=1):
        collection = self.get_or_create_collection("Question_Answer")
        # Reads typically don't lock the DB as much,
        # but if you still experience locking, you can wrap in a lock.
        with self.db_lock:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                # where_document={"$contains": keyword}
            )
        # Extract required lists
        questions = results.get('documents', [[]])[0]
        answers = [entry['answer'] for entry in results.get('metadatas', [[]])[0]]
        distances = results.get('distances', [[]])[0]
        return answers, questions

    def general_get_qa(self, query, services, n_results=1):
        collection = self.get_or_create_collection("Question_Answer")
        filter_conditions = [{"$not_contains": s} for s in services]
        with self.db_lock:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where_document={"$and": filter_conditions}
            )
        questions = results.get('documents', [[]])[0]
        answers = [entry['answer'] for entry in results.get('metadatas', [[]])[0]]
        distances = results.get('distances', [[]])[0]
        return answers, questions

    def get_all_documents(self, collection_name):
        collection = self.get_or_create_collection(collection_name)
        with self.db_lock:
            results = collection.query(
                query_texts=["*"],
                n_results=collection.count()
            )
        return [json.loads(doc) for doc in results['documents']]

    def add_question_answer(self, question, answer):
        self.add_qa("Question_Answer", question, {"answer": answer})
