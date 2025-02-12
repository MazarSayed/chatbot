import chromadb
from chromadb.config import Settings
import json
import yaml

class ChromaManager:
    def __init__(self, db_path):
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        self.client = chromadb.Client(Settings(persist_directory=db_path))
        self.collections = {}

    def get_or_create_collection(self, collection_name):
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(collection_name)
        return self.collections[collection_name]

    def add_qa(self, collection_name, content, metadata, id=None):
        collection = self.get_or_create_collection(collection_name)
        if id is None:
            id = str(collection.count() + 1)
        collection.add(
            documents=[json.dumps(content)],
            metadatas=[metadata],
            ids=[id]
        )

    def get_qa(self, collection_name, query, n_results):
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return [[entry['answer'] for sublist in results['metadatas'] for entry in sublist]],results
    
    def get_all_documents(self, collection_name):
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(
            query_texts=["*"],
            n_results=collection.count()
        )
        return [json.loads(doc) for doc in results['documents']]

    def add_question_answer(self, question, answer):
        self.add_qa("list_of_QA", question, {"answer": answer})

    def get_question_answer(self, question, n_results=1):
        return self.get_qa("list_of_QA", question, n_results)



 




