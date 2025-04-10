import os
from dotenv import load_dotenv
import json
import time
from groq import Groq
from src.utils.config import load_config
from src.nodes.functions import book_appointment,business_info
from tools import tools_calling
import streamlit as st
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from google.ai import generativelanguage as glm
from colorama import Style, Fore

config,prompt = load_config()
load_dotenv()

MODEL_NAME = "llama3-70b-8192"

PROMPT = """You are a helpful virtual dental concierge for a Dental Care Website owned by Brookline Progressive Dental Team \n
        - Your name is Luna, you are very patient, friendly and polite Dental Information provider.
        - if you call the 'business_info' tool you will get information regarding the Brookline Progressive Dental Team and types of Dental Services like: {services}, insurance, parking, make a payment or location etc.
        - if you call the 'book_appointment' tool an appointment form will be sent to the user to book an appointment with the Brookline Progressive Dental Team.
        - Make sure to analzye the chat_history and the input user_query before generating question_description 
        - Make sure you remember the last service user talked about, and use it to generate the right question_description """.format(services=config["services"])


def chat_with_llama(client, config, query, current_service, recent_history):
    """Process user query using Gemini API's function calling"""
    
    print(f"\n{'='*50}\n current_service in action: {current_service}\n{'='*50}")
    
    # Get the function declarations
    tools = tools_calling(config["services"], query, recent_history, current_service)

    # Create a new prompt message
    new_prompt = {
        "role": "user", 
        "parts": [{
            "text": f"""
                User query: {query}

                Based on this conversation and query, provide relevant information about dental services.
                Current service being discussed (if any): {current_service}
            """
        }]
    }
    
    # Create a copy of recent_history to avoid modifying the original
    formatted_messages = recent_history.copy()
    # Add the new prompt
    formatted_messages.append(new_prompt)
    
    # Call Gemini with function declarations using the correct structure
    try:
        # Configure with the proper format according to Gemini API
        generation_config = GenerateContentConfig(
            system_instruction=PROMPT,
            tools=tools
        )   
        # Make the API call using the tools
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=formatted_messages,
            config=generation_config
        )
        # Process function calls if any
        if hasattr(response, 'function_calls') and response.function_calls:
            # Extract function call info
            function_call = response.function_calls[0]
            function_name = function_call.name
            
            # Parse function args
            try:
                args = json.loads(function_call.args)
            except (TypeError, json.JSONDecodeError):
                args = function_call.args
            
            # Call the appropriate function
            if function_name == "business_info":
                service = args.get("dental_service", current_service if current_service != "None" else "")
                question = args.get("question_description", query)
                previous_service = args.get("previous_dental_service", "")
                return business_info(
                    dental_service=service,
                    question_description=question,
                    previous_dental_service=previous_service
                )
            elif function_name == "book_appointment":
                request = args.get("request", "Appointment booking request")
                return book_appointment(request=request)
        
        # If the model returned a regular text response or no function calls were detected
        if hasattr(response, 'text') and response.text:
            response_text = response.text
            if any(term in response_text for term in ["appointment", "schedule"]):
                return book_appointment(request=response_text)
            service = current_service if current_service != "None" else ""
            return business_info(
                dental_service=service,
                question_description=query,
                previous_dental_service=current_service
            )
            
        return [["No specific context found."], "None", query]
        
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return [["I'm having trouble processing your request."], "None", query]
