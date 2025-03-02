import chromadb
from chromadb.config import Settings
import json
import yaml
import os
import threading
import time
import numpy as np

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

    def service_get_qa(self, query_embedding, keyword, n_results=1):
        collection = self.get_or_create_collection("Question_Answer")
        with self.db_lock:
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
            )
        questions = results.get('documents', [[]])[0]
        answers = [entry['answer'] for entry in results.get('metadatas', [[]])[0]]
        return answers, questions

    def general_get_qa(self, query_embedding, services, n_results=1):
        collection = self.get_or_create_collection("Question_Answer")
        filter_conditions = [{"$not_contains": s} for s in services]
        with self.db_lock:
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,                
                where_document={"$and": filter_conditions}
            )
        questions = results.get('documents', [[]])[0]
        answers = [entry['answer'] for entry in results.get('metadatas', [[]])[0]]
        return answers, questions

    def get_all_documents(self, collection_name):
        collection = self.get_or_create_collection(collection_name)
        with self.db_lock:
            results = collection.query(
                query_texts=["*"],
                n_results=collection.count()
            )
        return [json.loads(doc) for doc in results['documents']]

    def add_question_answer(self, embedding, question, answer,buttons):
        self.add_qa("Question_Answer", question, embedding,{"answer": answer,"buttons": json.dumps(buttons)})

    def batch_add_question_answers(self, embeddings, questions, answers):
        """Add multiple QA pairs to the database in batches."""
        collection = self.get_or_create_collection("Question_Answer")
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(questions), batch_size):
            end_idx = min(i + batch_size, len(questions))
            batch_embeddings = [emb.tolist() for emb in embeddings[i:end_idx]]
            batch_questions = questions[i:end_idx]
            batch_answers = answers[i:end_idx]
            
            with self.db_lock:
                try:
                    collection.add(
                        embeddings=batch_embeddings,
                        documents=batch_questions,
                        metadatas=[{"answer": ans} for ans in batch_answers],
                        ids=[str(collection.count() + j + 1) for j in range(len(batch_questions))]
                    )
                    print(f"Added batch of {len(batch_questions)} items")
                except Exception as e:
                    print(f"Error adding batch: {e}")
