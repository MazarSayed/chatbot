import os
from dotenv import load_dotenv
import json
import time
from groq import Groq
from src.utils.config import load_config
from src.nodes.functions import service_testimonial,insurance_inquiry,general_question,service_costing
from tools import tools
import streamlit as st
config,prompt = load_config()
load_dotenv()

MODEL_NAME = "llama3-70b-8192"

PROMPT = """You are a python data scientist. you are given tasks to complete and you run python code to solve them.
- the python code runs in jupyter notebook.
- every time you call `execute_python` tool, the python code is executed in a separate cell. it's okay to multiple calls to `execute_python`.
- display visualizations using matplotlib or any other visualization library directly in the notebook. don't worry about saving the visualizations to a file.
- you have access to the internet and can make api requests.
- you also have access to the filesystem and can read/write files.
- you can install any pip package (if it exists) if you need to but the usual packages for data analysis are already preinstalled.
- you can run any python code you want, everything is running in a secure sandbox environment"""

SYSTEM_PROMPT = """ You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence\n
        - Your name is Luna, you are very patient, friendly and polite
        """

def chat_with_llama(user_message,groq_api_key):
    print(f"\n{'='*50}\nUser message: {user_message}\n{'='*50}")

    client = Groq(api_key=groq_api_key)
    messages = [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},]

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=tools(),
        tool_choice ="auto",
        temperature = 0,
        max_tokens = 4096,
        stream = False)

    response_message = response.choices[0].message
    messages.append(response_message)
    print(response_message)

    # Check if the model decided to use the provided function
    if not response_message.tool_calls:
        print("The model didn't use the function. Its response was:")
        print(response['message']['content'])
        return

    # Process function calls made by the model
    if response_message.tool_calls:
        available_functions = {
            'service_testimonial': service_testimonial,
            'insurance_inquiry': insurance_inquiry,
            'service_costing': service_costing,
            'general_question':general_question
            }

    for tool_call in response_message.tool_calls:
        function_name = tool_call.function.name
        print(function_name)
        if function_name in available_functions:
            function_to_call = available_functions[function_name]
        else:
            st.error(f"Function '{function_name}' not found in available_functions.")
        function_args = json.loads(tool_call.function.arguments)
        print(function_args)
        function_response = function_to_call(**function_args)
        print("Function_ouput:",function_response)
        # Add function response to the conversation
        messages.append(
            {
                "role": "assistant", 
                "content": str(function_response),
            }
        )

    # Second API call: Get final response from the model
    content_response = ""
    stream = client.chat.completions.create(model="llama3-70b-8192", messages=messages,temperature=0,stream=True)
    for chunk in stream:
        chunk = chunk.choices[0].delta.content
        time.sleep(0.075)
        if chunk:
            content_response += chunk
            yield chunk
    messages.append(content_response)         





