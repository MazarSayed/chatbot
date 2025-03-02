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

PROMPT = """You are a python data scientist. you are given tasks to complete and you run python code to solve them.
- the python code runs in jupyter notebook.
- every time you call `execute_python` tool, the python code is executed in a separate cell. it's okay to multiple calls to `execute_python`.
- display visualizations using matplotlib or any other visualization library directly in the notebook. don't worry about saving the visualizations to a file.
- you have access to the internet and can make api requests.
- you also have access to the filesystem and can read/write files.
- you can install any pip package (if it exists) if you need to but the usual packages for data analysis are already preinstalled.
- you can run any python code you want, everything is running in a secure sandbox environment"""



def chat_with_llama(client,query,recent_history):

    messages = [
        {"role":"system","content": prompt["system_prompt"]}]
    messages.extend(recent_history)

    user_message = {
        "role": "user",
        "content": f"Question: {query}"
    }
    messages.append(user_message)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=tools(config["services"],query,recent_history),
        tool_choice ="auto",
        temperature = 0,
        max_tokens = 4096,
        stream = False)

    response_message = response.choices[0].message
    messages.append(response_message)

    # Check if the model decided to use the provided function
    if not response_message.tool_calls:
        print("The model didn't use the function. Its response was:")
        print(response['message']['content'])
        return

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
        function_args = json.loads(tool_call.function.arguments)
        print(function_args)
        answers,question = function_to_call(**function_args)
        print("\n\nanswer:",answers,"\n\n result:",question)
        # Add function response to the conversation
        return answers,question    

    # Second API call: Get final response from the model
    #content_response = ""
    #stream = client.chat.completions.create(model="llama3-70b-8192", messages=messages,temperature=0,stream=True)
    #for chunk in stream:
    #    chunk = chunk.choices[0].delta.content
    #    time.sleep(0.075)
    #    if chunk:
    #        content_response += chunk
    #        yield chunk
    #messages.append(content_response)         


