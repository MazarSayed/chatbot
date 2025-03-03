from src.utils.config import load_config
from src.database.chroma_manager import ChromaManager
from typing_extensions import Annotated
import os
from src.utils.config import EmbeddingModel

def dental_services(dental_service: str,question_describtion:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    model = EmbeddingModel.get_instance()
    query_embedding = model.get_embedding(question_describtion)

    if dental_service in config["services"]:
        answers, questions, buttons = chroma_manager.service_get_qa(query_embedding, dental_service, 1)
    elif dental_service == '':
        answers, questions, buttons = general_question(question_describtion)
    else:
        answers = [[f"""Thank you for considering us for your dental needs! Unfortunately, 
            we do not currently offer {dental_service}. However, our dentists have an excellent network of specialists in this specialty. 
            We recommend coming in for a personalized assessment so our dentist can refer you to the right expert for your needs. 
            Would you like to schedule a consultation?"""]]
        questions = [[f"Services not in the list of {dental_service}"]]
        buttons = [[{}]]  # Empty buttons for services not in the list
    return answers, questions, buttons

def general_question(question_describtion:str)->str:
    config,prompt = load_config()
    model = EmbeddingModel.get_instance()
    query_embedding = model.get_embedding(question_describtion)
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    answers, questions, buttons = chroma_manager.general_get_qa(query_embedding, config["services"], 1)

    return answers, questions, buttons