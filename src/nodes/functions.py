from src.utils.config import load_config
from src.database.chroma_manager import ChromaManager
from typing_extensions import Annotated
import os

def dental_services(dental_service: str,user_query:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    if dental_service in config["services"]:
        answers,questions = chroma_manager.service_get_qa(user_query,dental_service,3)
    else:
        answers =[[f"""Thank you for considering us for your dental needs! Unfortunately, 
            we do not currently offer {dental_service}. However, our dentists have an excellent network of specialists in this specialty. 
            We recommend coming in for a personalized assessment so our dentist can refer you to the right expert for your needs. 
            Would you like to schedule a consultation?"""]]
        questions  = ""  
    return answers,questions

def general_question(user_query:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    answers,questions = chroma_manager.general_get_qa(user_query,config["services"],3)

    return answers,questions