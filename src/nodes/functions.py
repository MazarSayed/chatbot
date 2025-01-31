from src.utils.config import load_config
from src.utils.config import extract_insurances

def service_testimonial(dental_services: str)->str:
    config,prompt = load_config()
     
    output_message = prompt['testimony_prompt']
    return output_message


def insurance_inquiry(insurance:str,services:str=None)->str:
    config,prompt = load_config()

    Insurances = extract_insurances()
    
    output_message = f"Instructions:{prompt['insurance_prompt']}"+f"My Insurances:{insurance}" +f"Covered Insurances:{Insurances}" 
    return output_message


def general_question(query:str)->str:
    config,prompt = load_config()

    output_message = f"user_query:{query}\n"+f"Instructions:{prompt['qa_prompt']}"
    return output_message

def service_costing(service:str)->str:
    config,prompt = load_config()
     
    output_message = prompt['costing_prompt']
    return output_message