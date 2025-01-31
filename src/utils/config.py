import yaml
import json
from typing import Dict,Any
import os
import logging

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
    config_file_path = "/workspaces/chatbot/config/config.yaml"
    prompt_file_path = "/workspaces/chatbot/prompts/prompts.yaml"

    config = load_yaml(config_file_path)
    prompts = load_yaml(prompt_file_path)
    
    return config,prompts        



def extract_testimonials(input:str):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(dir_path, "..", '..', "data", "testimonials.yaml")
    testimonials = load_yaml(data_file_path)
    service_testimonials = []

    for testimonial in testimonials["testimonials"]:
        if input in testimonial["services"]:
            service_testimonials.append(testimonial["content"])
    return service_testimonials


def extract_insurances():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(dir_path, "..", '..', "data", "insurances.yaml")
    insurances = load_yaml(data_file_path)
    return insurances["insurance"]