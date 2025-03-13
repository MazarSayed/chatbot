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
        - if you call the 'business_info' tool you will get information regarding the Brookline Progressive Dental Team and types of Dental Services like: {}, insurance, parking or location etc.
        - if you call the 'book_appointment' tool an appointment form will be sent to the user to book an appointment with the Brookline Progressive Dental Team.
        - Make sure to analzye the chat_history and the input user_query before generating question_description 
        - Make sure you remember the last service user talked about, and use it to generate the right question_description """.format(config["services"])

def calculate_ceiling_tokens(tokens: int) -> int:
    """Calculate ceiling to nearest 1000 for token count"""
    return math.ceil(tokens / 1000) * 1000

def chat_with_llama(client, query, current_service, recent_history, logging_handler=None):
    # Initialize messages with system prompt
    messages = [
        {"role": "system", "content": PROMPT}]
    
    # Add conversation history to provide context for the model
    messages.extend(recent_history)

    print(f"\n{'='*50}\n current_service in action: {current_service}\n{'='*50}")

    # Add the current user query
    user_message = {
        "role": "user",
        "content": f"""Consider the chat_history:{recent_history} and mainly the user_query: {query} \n
                       Use the right tool and generate the right parameters based on the user_query,recent_history and current_service.\n
                       Link all insurance coverage questions to the current_service : {current_service} and make sure to answer for the service provided"""
    }
    messages.append(user_message)

    # Create the chat completion with the conversation history
    # The tools function now receives the recent_history to incorporate context
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=tools(config["services"], query, recent_history,current_service),
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
        print(response['message']['content'])
        return []

    # Process function calls made by the model
    if response_message.tool_calls:
        available_functions = {
            'business_info': business_info,
            'book_appointment': book_appointment
            }

    for tool_call in response_message.tool_calls:
        function_name = tool_call.function.name
        print(function_name)
        if function_name in available_functions:
            function_to_call = available_functions[function_name]
        else:
            st.error(f"Function '{function_name}' not found in available_functions.")
            return []
        function_args = json.loads(tool_call.function.arguments)
        print(function_args)
        answers,current_service = function_to_call(**function_args)
        print("\n\nTool answer:", answers)

        # Return based on function name
        if function_name == 'business_info':
            print("Context :",answers[0])
            print("Question :",answers[1])
            print("dental_service :",current_service)

            return answers,current_service,input_tokens,output_tokens  # Return both outputs for business_info
        elif function_name == 'book_appointment':
            return answers,current_service,input_tokens,output_tokens  # Return the appointment form

    # If we get here, something went wrong
    return [],current_service,input_tokens,output_tokens
