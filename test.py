import os
from dotenv import load_dotenv
import json
import time
from groq import Groq
from src.utils.config import load_config
from src.nodes.functions import dental_services,general_question
from tools import tools
import streamlit as st
config,prompt = load_config()
load_dotenv()

MODEL_NAME = "llama3-70b-8192"

PROMPT = """You are a helpful virtual dental concierge for a Dental Care Website owned by Brookline Progressive Dental Team \n
        - Your name is Luna, you are very patient, friendly and polite Dental Information provider.
        - if you call the 'service information' tool you will get information regarding various types of Dental Services like: {services} related to user teeth, not insurance, parking or location.
        - if you call the 'genral question' tool you will get infromation regarding other informations about the business like insurance, parking, location etc
        - Make sure to analzye the chat_history and the input user_query before generating query_description """



def chat_with_llama(client,query,recent_history):
    # Initialize messages with system prompt
    messages = [
        {"role":"system","content": prompt["system_prompt"].format(services=config["services"])}]
    
    # Add conversation history to provide context for the model
    messages.extend(recent_history)

    # Add the current user query
    user_message = {
        "role": "user",
        "content": f"Consider the chat_history:{recent_history} and mainly the user_query: {query}, use the right tool and generate the right parameters"
    }
    messages.append(user_message)

    # Create the chat completion with the conversation history
    # The tools function now receives the recent_history to incorporate context
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=tools(config["services"], query, recent_history),
        tool_choice="auto",
        temperature=0,
        max_tokens=4096,
        stream=False)

    # Get the response message and add it to the conversation
    response_message = response.choices[0].message
    messages.append(response_message)

    # Check if the model decided to use the provided function
    if not response_message.tool_calls:
        print("The model didn't use the function. Its response was:")
        print(response['message']['content'])
        return [], [], []

    # Process function calls made by the model
    if response_message.tool_calls:
        available_functions = {
            'dental_services': dental_services,
            'general_question': general_question
            }

    for tool_call in response_message.tool_calls:
        function_name = tool_call.function.name
        print(function_name)
        if function_name in available_functions:
            function_to_call = available_functions[function_name]
        else:
            st.error(f"Function '{function_name}' not found in available_functions.")
            return [], [], []
        function_args = json.loads(tool_call.function.arguments)
        print(function_args)
        answers, questions, buttons = function_to_call(**function_args)
        print("\n\nanswer:", answers, "\n\n result:", questions, "\n\n buttons:", buttons)
        # Add function response to the conversation
        return answers, questions, buttons
    
    # If we get here, something went wrong
    return [], [], []


