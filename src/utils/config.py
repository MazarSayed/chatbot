import yaml
import json
from typing import Dict,Any
import os
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from src.utils.docx_to_txt import convert_docs_to_markdown, read_folder_to_text_df
import math
import tiktoken

class EmbeddingModel:
    _instance = None
    _model = None
    _cache = {}  # Cache for embeddings

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if EmbeddingModel._model is None:
            logging.info("Loading embedding model...")
            # Use a smaller, faster model
            EmbeddingModel._model = SentenceTransformer('all-MiniLM-L6-v2')
            logging.info("Embedding model loaded successfully")

    def get_embedding(self, text):
        # Handle both single text and list of texts
        if isinstance(text, str):
            # Check cache for single text
            if text in self._cache:
                return self._cache[text]
            embedding = self._model.encode(text, normalize_embeddings=True)
            self._cache[text] = embedding
            return embedding
        else:
            # For list of texts, filter out cached ones
            uncached_texts = [t for t in text if t not in self._cache]
            if uncached_texts:
                new_embeddings = self._model.encode(uncached_texts, normalize_embeddings=True, batch_size=32)
                # Update cache with new embeddings
                for t, emb in zip(uncached_texts, new_embeddings):
                    self._cache[t] = emb
            # Return embeddings for all texts (from cache or newly computed)
            return [self._cache[t] for t in text]

def load_yaml(file_path):
    with open(file_path,'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
                print(f"Error reading {file_path}: {exc}")
                return None

def load_json(file_path):
    with open(file_path,'r') as stream:
        try:
            return json.load(stream)
        except json.JSONDecodeError as exc:
                print(f"Error reading {file_path}: {exc}")
                return None
        
def load_config() -> Dict[str, Any]:
    """
    Load configuration settings from YAML files.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_file_path = os.path.join(dir_path,"..","..","config" , "config.yaml")
    prompt_file_path = os.path.join(dir_path,"..","..","config" , "prompts.yaml")

    config = load_yaml(config_file_path)
    prompts = load_yaml(prompt_file_path)
    
    return config,prompts        

def load_question_answer():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    question_answer_path = os.path.join(dir_path,"..","..","data","question_answer.yaml")
    logging.debug("Loading qa's")
    question_answer = load_yaml(question_answer_path)
    return question_answer

def load_doc():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dental_implants_path = os.path.join(dir_path,"..","..","data","dental_implants.yaml")
    logging.debug("Loading doc's")
    dental_implants_doc = load_yaml(dental_implants_path)
    return dental_implants_doc[0]['Doc']

def populate_chroma_db_doc(chroma_manager):
    print("Populating Chroma DB with doc's...")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("dir_path",os.path.join(dir_path,"..","..","data/pdf/"))
    paragraphs = read_folder_to_text_df(os.path.join(dir_path,"..","..","data/pdf/"))
    #content = convert_docs_to_markdown(os.path.join(dir_path,"..","..","data/"))
    # Clean the extracted string
    #cleaned_text = [text for text in extracted_string if text.strip() and text != '\xa0']
    
    # Join the cleaned text into a single string
    #cleaned_text_string = '\n\n'.join(content)  # Join with double newlines if needed

    # Now you can safely call strip() and split()
    #words = content.strip().split()  # Split content into words
    #paragraphs = [' '.join(words[i:i + 100]) for i in range(0, len(words), 100)]  # Chunk into 100-word segments
    print(f"Number of paragraphs in the document: {len(paragraphs)}")
    
    model = EmbeddingModel.get_instance()
    embeddings = model.get_embedding(paragraphs)
    chroma_manager.batch_add_documents(embeddings, paragraphs)
    print("Chroma DB doc populated")

# Function to populate Chroma DB with examples
def populate_chroma_db(chroma_manager):
    logging.info("Populating Chroma DB with qa's...")
    print("Populating Chroma DB with qa's...")

    question_answer = load_question_answer()
    
    # Use singleton model instance
    model = EmbeddingModel.get_instance()
    
    # Prepare data for batch processing
    questions = [qa["question"] for qa in question_answer]
    answers = [qa["answer"] for qa in question_answer]
    buttons_list = [qa.get("buttons", {}) for qa in question_answer]  # Use get() with default empty dict
    
    # Get embeddings for all questions at once
    embeddings = model.get_embedding(questions)
    
    # Add all QAs in a single batch, including buttons
    chroma_manager.batch_add_question_answers(embeddings, questions, answers, buttons_list)
    
    print("Chroma DB qa populated")

def calculate_ceiling_tokens(tokens: int) -> int:
    """Calculate ceiling to nearest 1000 for token count"""
    return math.ceil(tokens / 1000) * 1000

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))