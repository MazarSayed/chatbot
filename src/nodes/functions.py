from src.utils.config import load_config
from src.database.chroma_manager import ChromaManager
import os

def dental_services(dental_service: str, user_message:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    if dental_service in config["services"]:
        retrieved_qa,results = chroma_manager.service_get_qa(user_message,dental_service,3)
    else:
        retrieved_qa =[[f"""Thank you for considering us for your dental needs! Unfortunately, 
            we do not currently offer {dental_service}. However, our dentists have an excellent network of specialists in this specialty. 
            We recommend coming in for a personalized assessment so our dentist can refer you to the right expert for your needs. 
            Would you like to schedule a consultation?"""]]
        results  = ""  
    return retrieved_qa,results

def general_question(user_message:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    retrieved_qa,results = chroma_manager.general_get_qa(user_message,config["services"],3)

    return retrieved_qa,results