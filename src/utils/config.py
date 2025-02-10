import yaml
import json
from typing import Dict,Any
import os
import logging
from pathlib import Path

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

# Function to populate Chroma DB with examples
def populate_chroma_db(chroma_manager):
    logging.info("Populating Chroma DB with qa's...")
    question_answer = load_question_answer()
    for qa in question_answer:
        chroma_manager.add_question_answer(qa["question"], qa["answer"])
        logging.debug(f"Added question-plan example: {qa['question']}")

    logging.info("Chroma DB populated")

def update_question_answer(chroma_manager):
    logging.info("Updating Chroma DB with qa's...")
    new_qa_list = load_question_answer()

    existing_entries = chroma_manager.get_all_documents("list_of_QA") 
    collection = chroma_manager.get_or_create_collection("list_of_QA")

    existing_data = {entry["question"]: entry["answer"] for entry in existing_entries}
    new_data = {qa["question"]: qa["answer"] for qa in new_qa_list}

    # Detect and update modified Q&A pairs
    for new_question, new_answer in new_data.items():
        if new_question not in existing_data or existing_data[new_question] != new_answer:
            # If question is new OR the answer has changed, remove old and add new
            existing_qa = chroma_manager.get_question_answer(new_question, n_results=1)

            if existing_qa:
                collection.delete([existing_qa[0]["id"]])  # Remove old entry

            # Add new or updated entry
            chroma_manager.add_question_answer(new_question, new_answer)
            print("Updated Question:",new_question)

    # Detect and remove deleted Q&A pairss
    for question in existing_data.keys():
        if question not in new_data:
            existing_qa = chroma_manager.get_question_answer(question, n_results=1)
            if existing_qa:
                collection.delete([existing_qa[0]["id"]]) 

    logging.info("Chroma DB Updated")
            