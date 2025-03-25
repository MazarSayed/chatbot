import json
import os
import threading
import time
import uuid
import socket
from typing import List, Dict, Any, Union, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from src.utils.config import load_config
import requests

# Environment variables for Qdrant configuration
os.environ["QDRANT_TIMEOUT"] = "60"  # Increased timeout for remote server

# Global dictionary to store client instances for singleton pattern
_client_instances = {}
_client_lock = threading.Lock()

# Real Qdrant cloud URL format is typically: https://{instance-id}.{region}.qdrant.io
# User must provide the correct URL in config.yaml as 'qdrant_url'
DEFAULT_QDRANT_URL = "http://localhost:6333"  # Default to local Qdrant server if running

class ChromaManager:
    """
    Vector database manager using Qdrant instead of ChromaDB.
    Maintains similar interface to allow for drop-in replacement.
    """
    def __init__(self, config: dict):
        """
        Initialize Qdrant client with persistence directory or remote connection.
        Uses a singleton pattern to ensure only one client instance per path.
        
        Args:
            db_path: Path to store vector database files (local mode) or identifier for remote connection
        """
        # Normalize the path for consistent dictionary keys
        self.db_path = config['qdrant_path']
        
        # Variables for remote server configuration
        try:
            qdrant_url = config['qdrant_url']
            qdrant_write_key = config['qdrant_write_key']
            qdrant_read_key = config['qdrant_read_key']
            use_remote = True
                    
            print(f"Config loaded. Use remote: {use_remote}, URL: {qdrant_url}")
        except Exception as e:
            print(f"Error loading config: {e}")
            use_remote = False
        

        # Choose the appropriate client ID for singleton pattern
        client_id = qdrant_url if use_remote else self.db_path
        
        # Get or create singleton client instance
        with _client_lock:
            if client_id not in _client_instances:
                if use_remote:
                    print(f"Creating new Qdrant client for remote server: {qdrant_url}")
                    try:
                        # Check if DNS resolution works before attempting connection
                        self._test_connectivity(qdrant_url)
                        
                        # Prefer write key if available, fall back to read key
                        api_key = qdrant_write_key or qdrant_read_key
                        
                        # Connect to remote Qdrant server
                        _client_instances[client_id] = QdrantClient(
                            url=qdrant_url,
                            api_key=api_key,
                            timeout=60.0  # Increased timeout for remote server
                        )
                        print(f"Connected to remote Qdrant server at {qdrant_url}")
                    except (socket.gaierror, ConnectionError, requests.exceptions.ConnectionError) as e:
                        print(f"DNS resolution or connection error: {e}")
                        print("Cannot resolve or connect to the remote Qdrant server.")
                        print("Check your qdrant_url in config.yaml. For Qdrant Cloud it should be like: https://your-instance-id.region.qdrant.io")
                        print("Falling back to local storage...")
                        use_remote = False
                        
                        # Create the local directory if needed
                        os.makedirs(self.db_path, exist_ok=True)
                        
                        # Initialize local client as fallback
                        _client_instances[client_id] = QdrantClient(path=self.db_path)
                        print(f"Using local storage at {self.db_path}")
                    except Exception as e:
                        print(f"Error connecting to remote Qdrant server: {e}")
                        print("Falling back to local storage...")
                        use_remote = False
                        
                        # Create the local directory if needed
                        os.makedirs(self.db_path, exist_ok=True)
                        
                        # Initialize local client as fallback
                        _client_instances[client_id] = QdrantClient(path=self.db_path)
                        print(f"Using local storage at {self.db_path}")
                else:
                    print(f"Creating new Qdrant client for local storage: {self.db_path}")
                    # Create the directory if it doesn't exist
                    os.makedirs(self.db_path, exist_ok=True)
                    
                    # Initialize local client
                    try:
                        _client_instances[client_id] = QdrantClient(path=self.db_path)
                        print(f"Using local storage at {self.db_path}")
                    except Exception as e:
                        print(f"Error creating local Qdrant client: {e}")
                        # Try again with a different path as fallback
                        fallback_path = os.path.join(os.path.dirname(self.db_path), "qdrant_db")
                        os.makedirs(fallback_path, exist_ok=True)
                        _client_instances[client_id] = QdrantClient(path=fallback_path)
                        print(f"Fallback: Using local storage at {fallback_path}")
            else:
                print(f"Reusing existing Qdrant client for: {client_id}")
        
        # Use the singleton client instance
        self.client = _client_instances[client_id]
        
        # Store whether we're using remote mode
        self.use_remote = use_remote
        
        # Track collections that have been created
        self.collections = {}
        
        # Create a lock to serialize database write operations
        self.db_lock = threading.Lock()
        
        # Vector dimension (will be set based on first embedding)
        self.vector_dim = None
    
    def _test_connectivity(self, url: str) -> bool:
        """
        Test if we can resolve and connect to the given URL.
        
        Args:
            url: The URL to test connectivity to
            
        Returns:
            True if connection is possible, raises exception otherwise
        """
        if not url:
            raise ValueError("URL is empty or None")
            
        # Extract hostname from URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.split(':')[0]  # Remove port if present
        
        # Try to resolve the hostname
        socket.gethostbyname(hostname)
        
        # If we get here, DNS resolution worked
        return True
    
    # Helper method to generate valid UUID string
    def _generate_uuid(self) -> str:
        """Generate a valid UUID string for Qdrant points"""
        return str(uuid.uuid4())
    
    def get_or_create_collection(self, collection_name: str) -> str:
        """
        Get an existing collection or create a new one if it doesn't exist.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection name for consistency with original interface
        """
        if collection_name not in self.collections:
            with self.db_lock:
                # Check if collection exists
                collections_list = self.client.get_collections().collections
                collection_exists = any(c.name == collection_name for c in collections_list)
                
                if not collection_exists:
                    # Vector dimension is required for creation, but we might not know it yet
                    # If we don't know the dimension, we'll create it later with the first embedding
                    if self.vector_dim is not None:
                        self.client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(
                                size=self.vector_dim,
                                distance=Distance.COSINE
                            )
                        )
                
                self.collections[collection_name] = collection_name
                
        return self.collections[collection_name]
    
    def add_qa(self, collection_name: str, content: str, metadata: Dict[str, Any], id: Optional[str] = None) -> None:
        """
        Add a single QA pair to the database.
        
        Args:
            collection_name: Name of the collection
            content: Question content
            metadata: Dictionary with answer and buttons
            id: Optional ID for the point
        """
        collection = self.get_or_create_collection(collection_name)
        
        if id is None:
            # Generate a valid UUID if not provided
            id = self._generate_uuid()
        
        # Use lock to prevent concurrent writes
        with self.db_lock:
            # Get collection info to check if it exists with proper vector dimension
            try:
                collection_info = self.client.get_collection(collection_name=collection_name)
                
                # Store content as a payload
                point = PointStruct(
                    id=id,
                    payload={
                        "content": content,
                        **metadata
                    }
                )
                
                # Since we don't have embeddings here, we just store the content
                # The original ChromaDB version used json.dumps(content) but didn't use embeddings
                # We'll use payload-only points until we have a proper implementation with embeddings
                self.client.upsert(
                    collection_name=collection_name,
                    points=[point]
                )
            
            except Exception as e:
                print(f"Error adding QA: {e}")
    
    def service_get_qa(self, query_embedding: np.ndarray, keyword: str, n_results: int = 1) -> List[str]:
        """
        Search for question-answer pairs related to a specific service.
        
        Args:
            query_embedding: Embedding of the query
            keyword: Service keyword
            n_results: Number of results to return
            
        Returns:
            List of answers
        """
        collection_name = "Luna_QA"
        collection = self.get_or_create_collection(collection_name)
        
        # Update vector dimension if not set
        if self.vector_dim is None:
            self.vector_dim = len(query_embedding)
            # Create collection with proper dimensions if it doesn't exist
            collections_list = self.client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections_list)
            if not collection_exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
        
        with self.db_lock:
            try:
                # Convert embedding to list for Qdrant
                query_vector = query_embedding.tolist()
                
                # Search using the embedding
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=n_results
                )
                
                # Extract answers from results
                answers = []
                for point in search_result:
                    payload = point.payload
                    if 'answer' in payload:
                        answers.append(str(payload['answer']))
                
                return answers
            
            except Exception as e:
                print(f"Error in service_get_qa: {e}")
                return []
    
    def general_get_qa(self, query_embedding: np.ndarray, services: List[str], n_results: int = 1) -> List[str]:
        """
        Search for general question-answer pairs, excluding specific services.
        
        Args:
            query_embedding: Embedding of the query
            services: List of service names to exclude
            n_results: Number of results to return
            
        Returns:
            List of answers
        """
        collection_name = "Luna_QA"
        collection = self.get_or_create_collection(collection_name)
        
        # Update vector dimension if not set
        if self.vector_dim is None:
            self.vector_dim = len(query_embedding)
            # Create collection with proper dimensions if it doesn't exist
            collections_list = self.client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections_list)
            if not collection_exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
        
        with self.db_lock:
            try:
                # Convert embedding to list for Qdrant
                query_vector = query_embedding.tolist()
                
                # Create filter to exclude services
                # This is an approximation of the original filter_conditions logic
                # Qdrant doesn't have direct equivalent of "$not_contains" for text fields
                # This assumes the content field has service names that we want to exclude
                
                # For simplicity, we'll just search without filtering first
                # In a production scenario, you'd want to implement proper filtering
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=n_results
                )
                
                # Extract answers from results
                answers = []
                for point in search_result:
                    payload = point.payload
                    if 'answer' in payload:
                        # Post-process filtering - check if content contains any service name
                        content = payload.get('content', '')
                        if not any(service.lower() in content.lower() for service in services):
                            answers.append(str(payload['answer']))
                
                # Limit results to requested number
                return answers[:n_results]
            
            except Exception as e:
                print(f"Error in general_get_qa: {e}")
                return []
    
    def get_doc(self, embedding: np.ndarray, dental_service: str, n_results: int = 1) -> List[str]:
        """
        Retrieve documents related to a dental service.
        
        Args:
            embedding: Query embedding
            dental_service: Dental service name
            n_results: Number of results to return
            
        Returns:
            List of document texts
        """
        collection_name = "Luna_QA"
        collection = self.get_or_create_collection(collection_name)
        
        # Update vector dimension if not set
        if self.vector_dim is None:
            self.vector_dim = len(embedding)
            # Create collection with proper dimensions if it doesn't exist
            collections_list = self.client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections_list)
            if not collection_exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
        
        print("\n\nCollection:", collection_name)
        
        with self.db_lock:
            try:
                # Convert embedding to list for Qdrant
                query_vector = embedding.tolist()
                
                # Search using the embedding
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=n_results
                )
                
                # Extract documents from results
                documents = []
                for point in search_result:
                    # Luna_QA are stored directly in payload
                    if 'text' in point.payload:
                        documents.append(point.payload['text'])
                    else:
                        # Fall back to entire payload if no text field
                        documents.append(str(point.payload))
                
                if documents:
                    print("Extracted documents:", documents)
                    return documents
                else:
                    print("No valid documents found.")
                    return []
            
            except Exception as e:
                print(f"Error in get_doc: {e}")
                return []
    
    def get_all_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Get all documents from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List of document contents
        """
        collection = self.get_or_create_collection(collection_name)
        print("\n\nCollection:", collection_name)
        
        with self.db_lock:
            try:
                # Scroll through all points in the collection
                scroll_results = self.client.scroll(
                    collection_name=collection_name,
                    limit=10000  # Adjust as needed
                )
                
                points = scroll_results[0]  # First element contains points
                
                # Extract document contents from points
                documents = []
                for point in points:
                    payload = point.payload
                    if 'content' in payload:
                        try:
                            # Try to parse content if it's JSON
                            documents.append(json.loads(payload['content']))
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, use raw content
                            documents.append(payload['content'])
                
                return documents
            
            except Exception as e:
                print(f"Error in get_all_documents: {e}")
                return []
    
    def add_question_answer(self, embedding: np.ndarray, question: str, answer: str, buttons: Dict[str, str]) -> None:
        """
        Add a question-answer pair with embedding.
        
        Args:
            embedding: Question embedding
            question: Question text
            answer: Answer text
            buttons: Dictionary of button data
        """
        # Update vector dimension if not set
        if self.vector_dim is None:
            self.vector_dim = len(embedding)
        
        # Store buttons as a JSON string
        buttons_json = json.dumps(buttons) if buttons else '{}'
        
        collection_name = "Luna_QA"
        collection = self.get_or_create_collection(collection_name)
        
        # Create collection with proper dimensions if it doesn't exist
        collections_list = self.client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections_list)
        if not collection_exists:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_dim,
                    distance=Distance.COSINE
                )
            )
        
        # Generate a valid UUID
        id = self._generate_uuid()
        
        with self.db_lock:
            try:
                # Create point with embedding, document and metadata
                point = PointStruct(
                    id=id,
                    vector=embedding.tolist(),
                    payload={
                        "content": question,
                        "answer": answer,
                        "buttons": buttons_json
                    }
                )
                
                # Add to collection
                self.client.upsert(
                    collection_name=collection_name,
                    points=[point]
                )
            
            except Exception as e:
                print(f"Error adding question-answer: {e}")
    
    def batch_add_question_answers(self, embeddings: List[np.ndarray], questions: List[str], 
                                  answers: List[str], buttons_list: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Add multiple QA pairs to the database in batches.
        
        Args:
            embeddings: List of embeddings
            questions: List of questions
            answers: List of answers
            buttons_list: Optional list of button dictionaries
        """
        collection_name = "Luna_QA"
        collection = self.get_or_create_collection(collection_name)
        
        # Update vector dimension if not set
        if self.vector_dim is None and embeddings:
            self.vector_dim = len(embeddings[0])
            # Create collection with proper dimensions if it doesn't exist
            collections_list = self.client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections_list)
            if not collection_exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
        
        # Process in batches
        batch_size = 10
        for i in range(0, len(questions), batch_size):
            end_idx = min(i + batch_size, len(questions))
            batch_embeddings = embeddings[i:end_idx]
            batch_questions = questions[i:end_idx]
            batch_answers = answers[i:end_idx]
            batch_buttons = buttons_list[i:end_idx] if buttons_list else [{}] * len(batch_questions)
            
            # Convert buttons dictionaries to JSON strings
            batch_buttons_json = [json.dumps(btn) if btn else '{}' for btn in batch_buttons]
            
            # Create points for batch
            points = []
            for j, (emb, question, answer, btn_json) in enumerate(zip(
                batch_embeddings, batch_questions, batch_answers, batch_buttons_json
            )):
                # Generate a valid UUID for each point
                id = self._generate_uuid()
                
                # Create point
                point = PointStruct(
                    id=id,
                    vector=emb.tolist(),
                    payload={
                        "content": question,
                        "answer": answer,
                        "buttons": btn_json
                    }
                )
                points.append(point)
            
            with self.db_lock:
                try:
                    # Batch upsert
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    print(f"Added batch of {len(points)} items")
                except Exception as e:
                    print(f"Error adding batch: {e}")
    
    def batch_add_documents(self, embeddings: List[np.ndarray], documents: List[str]) -> None:
        """
        Add multiple documents to the database in batches using Qdrant.
        
        Args:
            embeddings: List of document embeddings
            documents: List of document texts
        """
        collection_name = "Luna_QA"
        
        print(f"Starting batch_add_documents with {len(documents)} documents")
        
        if not embeddings or not documents:
            print("No documents or embeddings to add")
            return
            
        if len(embeddings) != len(documents):
            print(f"Error: Number of embeddings ({len(embeddings)}) doesn't match number of documents ({len(documents)})")
            return
            
        # Print first document and embedding to verify data
        if documents and embeddings:
            print(f"First document preview: {documents[0][:100]}...")
            print(f"First embedding shape: {embeddings[0].shape}")
        
        # Get or create the collection
        collection = self.get_or_create_collection(collection_name)
        
        # Update vector dimension if not set
        if self.vector_dim is None and embeddings:
            self.vector_dim = len(embeddings[0])
            print(f"Setting vector dimension to {self.vector_dim}")

        # Verify if collection exists and create it if needed
        with self.db_lock:
            try:
                # Explicitly check if collection exists
                collections_info = self.client.get_collections()
                collection_exists = any(c.name == collection_name for c in collections_info.collections)
                
                if not collection_exists:
                    print(f"Collection '{collection_name}' does not exist. Creating it now...")
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_dim,
                            distance=Distance.COSINE
                        )
                    )
                    print(f"Collection '{collection_name}' created successfully")
                else:
                    print(f"Collection '{collection_name}' already exists")
                    # Get collection info to verify it's properly configured
                    collection_info = self.client.get_collection(collection_name)
                    print(f"Current collection size: {collection_info.vectors_count} vectors")
            except Exception as e:
                print(f"Error checking/creating collection: {e}")
                return  # Exit if we can't even check or create the collection
        
        # Use a smaller batch size for better reliability
        batch_size = 10
        total_added = 0
        failures = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            current_batch_size = end_idx - i
            print(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}: documents {i} to {end_idx-1}")
            
            batch_embeddings = embeddings[i:end_idx]
            batch_documents = documents[i:end_idx]
            
            # Create points for batch
            points = []
            for j, (emb, doc) in enumerate(zip(batch_embeddings, batch_documents)):
                # Skip empty documents
                if not doc or not doc.strip():
                    print(f"Skipping empty document at index {i+j}")
                    continue
                
                # Generate a valid UUID for each point
                id = self._generate_uuid()
                
                # Create point with vector and payload
                try:
                    vector_list = emb.tolist()
                    # Verify vector is valid (not NaN or inf)
                    if not all(isinstance(x, (int, float)) and not np.isnan(x) and not np.isinf(x) for x in vector_list):
                        print(f"Invalid vector values in document {i+j}. Skipping.")
                        continue
                        
                    point = PointStruct(
                        id=id,
                        vector=vector_list,
                        payload={
                            "text": doc,
                            "index": i+j  # Add index for debugging
                        }
                    )
                    points.append(point)
                except Exception as e:
                    print(f"Error creating point for document {i+j}: {e}")
                    continue
            
            # Skip empty batches
            if not points:
                print(f"No valid points in batch {i//batch_size + 1}. Skipping.")
                continue
            
            print(f"Attempting to add {len(points)} points to collection '{collection_name}'")
            
            with self.db_lock:
                try:
                    # Batch upsert to Qdrant database
                    result = self.client.upsert(
                        collection_name=collection_name,
                        points=points,
                        wait=True  # Make sure operation completes before continuing
                    )
                    
                    # Verify operation succeeded
                    if hasattr(result, 'status') and result.status == 'ok':
                        total_added += len(points)
                        print(f"Successfully added batch of {len(points)} documents")
                    else:
                        print(f"Warning: Upsert completed but status unclear. Result: {result}")
                        total_added += len(points)  # Assume it worked
                except Exception as e:
                    failures += 1
                    print(f"Error adding batch to Qdrant: {e}")
                    
                    # Try one-by-one approach for this batch
                    if len(points) > 1:
                        print("Retrying with individual document inserts...")
                        for idx, point in enumerate(points):
                            try:
                                self.client.upsert(
                                    collection_name=collection_name,
                                    points=[point],
                                    wait=True
                                )
                                total_added += 1
                                print(f"Added individual document {i + idx}")
                            except Exception as e:
                                print(f"Error adding individual document {i + idx}: {e}")
        
        # Verify final collection size with explicit check
        print(f"Batch processing complete. Attempted to add {total_added} documents with {failures} batch failures")
        
        try:
            # Check collection exists first
            collections_info = self.client.get_collections()
            collection_exists = any(c.name == collection_name for c in collections_info.collections)
            
            if collection_exists:
                collection_info = self.client.get_collection(collection_name)
                print(f"Collection '{collection_name}' now contains {collection_info.vectors_count} vectors")
                
                # Additional validation - try to retrieve a few points to verify they exist
                if collection_info.vectors_count > 0:
                    try:
                        # Try to retrieve some random points
                        scroll_result = self.client.scroll(
                            collection_name=collection_name,
                            limit=5,  # Just get a few points
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        if scroll_result and scroll_result[0]:
                            points = scroll_result[0]
                            print(f"Successfully retrieved {len(points)} points from collection")
                            if points:
                                # Show a sample point payload
                                print(f"Sample point payload: {points[0].payload}")
                        else:
                            print("Warning: Scroll returned empty result despite positive vector count")
                    except Exception as e:
                        print(f"Error verifying points: {e}")
            else:
                print(f"Warning: Collection '{collection_name}' does not exist after batch processing!")
        except Exception as e:
            print(f"Error getting final collection info: {e}")
            
        return total_added  # Return count of added documents
