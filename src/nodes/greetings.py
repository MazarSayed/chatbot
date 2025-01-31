import logging
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from src.utils.config import load_config
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

def greeting(groq_api_key):
    load_dotenv()
    logging.info("Greetings")
    api_key = groq_api_key

    config,prompt = load_config()
    model = ChatGroq(
                model="llama3-70b-8192",
                api_key=api_key
                )
    Business = config['owner']
    Services = config['services']
    
    
    prompt = ChatPromptTemplate.from_messages([
            ("system", prompt['system_prompt']),
            ("human", prompt['greeting_prompt'])
        ])
    
    greeting =  prompt | model | JsonOutputParser()
    response = greeting.invoke({"Business": Business, "Services":Services})
    output_message = (
    f"{response['Greeting']}\n\n"  # Add a line break after the greeting
    f"{response['Services']}\n\n"  # Add a line break after the services question
    "Our Services:\n"  # Title for the services section
    + "\n".join(f"- {service}" for service in response["JSON_services"])  # List services with bullet points
    )
    return output_message