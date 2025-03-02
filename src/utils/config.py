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
def populate_chroma_db(client, chroma_manager):
    logging.info("Populating Chroma DB with qa's...")
    question_answer = load_question_answer()

    for qa in question_answer:
        embedding = get_embedding(client, qa["question"])
        chroma_manager.add_question_answer(embedding,qa["question"], qa["answer"], qa["buttons"])
        logging.debug(f"Added question-plan example: {qa['question']}")

    logging.info("Chroma DB populated")


def get_embedding(client,text):
    response = client.embeddings.create(
        model="llama2-70b-4096",
        input=text
    )
    return response.data[0].embedding            