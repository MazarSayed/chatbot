from src.utils.config import load_config
from src.utils.config import extract_insurances

def service_testimonial(dental_services: str)->str:
    config,prompt = load_config()
     
    output_message = prompt['testimony_prompt']
    return output_message


def insurance_inquiry(insurance:str)->str:
    config,prompt = load_config()

    Insurances = extract_insurances()
    if insurance not in Insurances:
        output_message =  f"Provide a sorry message and Provide the list of insrances we cover {Insurances}"
    else:
        output_message = f"My Insurances:{insurance}"+"\n"+f"Covered Insurances:{Insurances}"+"\n"+ f"Instructions:{prompt['insurance_prompt']}"
    return output_message


def general_question(query:str)->str:
    config,prompt = load_config()

    output_message = f"user_query:{query}\n"+f"Instructions:{prompt['qa_prompt']}"
    return output_message

def service_costing()->str:
    config,prompt = load_config()
     
    output_message = prompt['costing_prompt']
    return output_message