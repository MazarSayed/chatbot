import os
from dotenv import load_dotenv
import json
import time
from groq import Groq
from src.utils.config import load_config
from src.nodes.functions import book_appointment, business_info
from tools import tools
import streamlit as st
from src.handlers.logging_handler import LLMLoggingHandler
import math

config, prompt = load_config()
load_dotenv()

MODEL_NAME = "llama3-70b-8192"

PROMPT = """You are a helpful virtual dental concierge for a Dental Care Website owned by Brookline Progressive Dental Team \n
        - Your name is Luna, you are very patient, friendly and polite Dental Information provider.
        - if you call the 'business_info' tool you will get information regarding the Brookline Progressive Dental Team and types of Dental Services like: {services}, insurance, parking or location etc.
        - if you call the 'book_appointment' tool an appointment form will be sent to the user to book an appointment with the Brookline Progressive Dental Team.
        - Make sure to analzye the chat_history and the input user_query before generating query_description """.format(services=config["services"])

def calculate_ceiling_tokens(tokens: int) -> int:
    """Calculate ceiling to nearest 1000 for token count"""
    return math.ceil(tokens / 1000) * 1000

def chat_with_llama(client, query, current_service, recent_history, logging_handler=None):
    # Initialize messages with system prompt
    messages = [
        {"role": "system", "content": PROMPT}]
    
    # Add conversation history to provide context for the model
    messages.extend(recent_history)

    # Add the current user query
    user_message = {
        "role": "user",
        "content": f"Consider the chat_history:{recent_history} and mainly the user_query: {query}, use the right tool and generate the right parameters, current_service: {current_service}"
    }
    messages.append(user_message)

    # Create the chat completion with the conversation history
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=tools(config["services"], query, recent_history, current_service),
        tool_choice="auto",
        temperature=0,
        max_tokens=4096,
        stream=False)

    # Get token usage from response
    token_usage = response.usage
    input_tokens = calculate_ceiling_tokens(token_usage.prompt_tokens)
    output_tokens = calculate_ceiling_tokens(token_usage.completion_tokens)

    # If we have a logging handler, update token counts
    if logging_handler:
        logging_handler.update_token_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name="llama3-70b-8192"
        )

    # Get the response message and add it to the conversation
    response_message = response.choices[0].message
    messages.append(response_message)

    # Check if the model decided to use the provided function
    if not response_message.tool_calls:
        print("The model didn't use the function. Its response was:")
        print(response.choices[0].message.content)
        return []

    # Process function calls made by the model
    if response_message.tool_calls:
        available_functions = {
            'business_info': business_info,
            'book_appointment': book_appointment
        }

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            print(f"Function called: {function_name}")
            
            if function_name in available_functions:
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                print(f"Function arguments: {function_args}")
                
                answer,dental_service = function_to_call(**function_args)
                print(f"\nTool answer: {answer}")

                if function_name == 'business_info':
                    # For business info, return context and service for RAG
                    return answer, dental_service, {"input_tokens": input_tokens, "output_tokens": output_tokens}
                elif function_name == 'book_appointment':
                    # For appointment, return the form directly
                    return answer, dental_service, {"input_tokens": input_tokens, "output_tokens": output_tokens}

    # If we get here, something went wrong
    return "", None, {"input_tokens": input_tokens, "output_tokens": output_tokens}
