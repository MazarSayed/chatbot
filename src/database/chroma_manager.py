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
        collection = self.get_or_create_collection("Question__Answer")
        with self.db_lock:
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
            )
        
        # Initialize default return values
        questions = ""
        answers = []
        buttons = []

        # Get documents/questions
        documents = results.get('documents', [[]])
        if documents and documents[0]:  # Check if we have any documents
            questions = str(documents[0][0]) if isinstance(documents[0], list) else str(documents[0])

        # Get metadata (answers and buttons)
        metadatas = results.get('metadatas', [[]])
        if metadatas and metadatas[0]:  # Check if we have any metadata
            metadata = metadatas[0][0] if isinstance(metadatas[0], list) else metadatas[0]
            
            # Extract answer
            answer = metadata.get('answer', '')
            if answer:
                answers = [str(answer)]

            # Extract buttons
            try:
                buttons_data = metadata.get('buttons', {})
                print("Raw buttons:", buttons_data)
                if isinstance(buttons_data, dict):
                    # If it's already a dictionary, use it directly
                    buttons = [{"text": key, "action": value} for key, value in buttons_data.items() if key and value]
                elif isinstance(buttons_data, str):
                    # Try to parse as JSON if it's a string
                    try:
                        buttons_dict = json.loads(buttons_data)
                        buttons = [{"text": key, "action": value} for key, value in buttons_dict.items() if key and value]
                    except json.JSONDecodeError:
                        buttons = []
            except (TypeError, AttributeError) as e:
                print(f"Error processing buttons: {e}")
                buttons = []
            
            print("Processed buttons:", buttons)

        return answers

    def general_get_qa(self, query_embedding, services, n_results=1):
        collection = self.get_or_create_collection("Question__Answer")
        filter_conditions = [{"$not_contains": s} for s in services]
        with self.db_lock:
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,                
                where_document={"$and": filter_conditions}
            )
        
        # Initialize default return values
        questions = ""
        answers = []
        buttons = []

        # Get documents/questions
        documents = results.get('documents', [[]])
        if documents and documents[0]:  # Check if we have any documents
            questions = str(documents[0][0]) if isinstance(documents[0], list) else str(documents[0])

        # Get metadata (answers and buttons)
        metadatas = results.get('metadatas', [[]])
        if metadatas and metadatas[0]:  # Check if we have any metadata
            metadata = metadatas[0][0] if isinstance(metadatas[0], list) else metadatas[0]
            
            # Extract answer
            answer = metadata.get('answer', '')
            if answer:
                answers = [str(answer)]

            # Extract buttons
            try:
                buttons_data = metadata.get('buttons', {})
                print("Raw buttons:", buttons_data)
                if isinstance(buttons_data, dict):
                    # If it's already a dictionary, use it directly
                    buttons = [{"text": key, "action": value} for key, value in buttons_data.items() if key and value]
                elif isinstance(buttons_data, str):
                    # Try to parse as JSON if it's a string
                    try:
                        buttons_dict = json.loads(buttons_data)
                        buttons = [{"text": key, "action": value} for key, value in buttons_dict.items() if key and value]
                    except json.JSONDecodeError:
                        buttons = []
            except (TypeError, AttributeError) as e:
                print(f"Error processing buttons: {e}")
                buttons = []
            
            print("Processed buttons:", buttons)

        return answers
    
    def get_doc(self, embedding, dental_service,n_results=1):
        """Retrieve documents from the specified collection based on a query."""
        collection = self.get_or_create_collection("Documents")
        print("\n\nCollection:", collection)
        with self.db_lock:
            results = collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=n_results,
            )
        
        # Extract documents from results
        Documents = results.get('documents', [[]])
        if Documents and isinstance(Documents, list) and isinstance(Documents[0], list):
            extracted_string = Documents[0]  # Access the first element of the first list
            print("Extracted String:", extracted_string)
        else:
            print("No valid documents found.")
        # If documents are strings, parse them
        return extracted_string # Return non-empty documents

    def get_all_documents(self, collection_name):
        collection = self.get_or_create_collection(collection_name)
        print("\n\nCollection:", collection)
        with self.db_lock:
            results = collection.query(
                query_texts=["*"],
                n_results=collection.count()
            )
        return [json.loads(doc) for doc in results['documents']]

    def add_question_answer(self, embedding, question, answer, buttons):
        # Store buttons as a JSON string
        buttons_json = json.dumps(buttons) if buttons else '{}'
        self.add_qa("Question_Answer", question, {"answer": answer, "buttons": buttons_json}, None)

    def batch_add_question_answers(self, embeddings, questions, answers, buttons_list=None):
        """Add multiple QA pairs to the database in batches."""
        collection = self.get_or_create_collection("Question__Answer")
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(questions), batch_size):
            end_idx = min(i + batch_size, len(questions))
            batch_embeddings = [emb.tolist() for emb in embeddings[i:end_idx]]
            batch_questions = questions[i:end_idx]
            batch_answers = answers[i:end_idx]
            batch_buttons = buttons_list[i:end_idx] if buttons_list else [{}] * len(batch_questions)
            
            # Convert buttons dictionaries to JSON strings
            batch_buttons_json = [json.dumps(btn) if btn else '{}' for btn in batch_buttons]
            
            with self.db_lock:
                try:
                    collection.add(
                        embeddings=batch_embeddings,
                        documents=batch_questions,
                        metadatas=[{"answer": ans, "buttons": btn_json} for ans, btn_json in zip(batch_answers, batch_buttons_json)],
                        ids=[str(collection.count() + j + 1) for j in range(len(batch_questions))]
                    )
                    print(f"Added batch of {len(batch_questions)} items")
                except Exception as e:
                    print(f"Error adding batch: {e}")

    def batch_add_documents(self, embeddings, documents):
        """Add multiple documents to the database in batches."""
        collection = self.get_or_create_collection("Documents")
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_embeddings = [emb.tolist() for emb in embeddings[i:end_idx]]
            batch_documents = documents[i:end_idx]
            

            with self.db_lock:
                try:
                    collection.add(
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        ids=[str(collection.count() + j + 1) for j in range(len(batch_documents))]
                    )
                    print(f"Added batch of {len(batch_documents)} documents")
                except Exception as e:
                    print(f"Error adding batch: {e}")       
