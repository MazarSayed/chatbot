from groq import Groq
import time
from test import chat_with_llama
from src.utils.config import calculate_ceiling_tokens,count_tokens
from src.utils.config import load_config
import asyncio
import streamlit as st



async def rag(client, query, groq_api_key, current_service, chat_history):
    config, prompt = load_config()

    if len(chat_history) > 7:
        recent_history = chat_history[-7:]
    else:
        recent_history = chat_history[:]

    # Get response from chat_with_llama
    answer, dental_service, input_tokens, output_tokens = chat_with_llama(client, query, current_service, recent_history)
    
    # Handle appointment form case
    if isinstance(answer, dict):
        return answer, dental_service, input_tokens, output_tokens

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Brookline Dental Team. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "Use the given Context to generate a response to the question in detail"
                "Provide a short answers in a structred format with appropriate line breaks and bolds only when needed."
                "Makse sure curate your response to showcase the brand of Brookline Dental Team"
                "Here is your welcome message = {}".format(config['welcome_message'])
            )
        }
    ]
    messages.extend(recent_history)

    user_message = {
        "role": "user",
        "content": f""" 
                    My_Question: {answer[1]}\n
                    Context: {answer[0]}. \n
                    dental_service: {dental_service}

                    Follow the steps given below:
                        1. Analyze My_Question and Context given above.
                        2. Provide a response to answer My_Question using the Context mainly.
                        3. Output your short response in the structured format with appropriate line breaks and bolds only when needed.

                    Note: Provide very detailed long answers for questions only on treatment plan and after care for the dental services
                    Provide only the output by following above steps with no additional text.
                    """
    }
    messages.append(user_message)

    # Get streaming response from LLM
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.5,
        max_tokens=8192,
        stream=True)

    chat_input_tokens = calculate_ceiling_tokens(count_tokens(str(messages)))
    total_input_tokens = input_tokens + chat_input_tokens

    return response, dental_service, total_input_tokens

async def stream_response(response_text, delay):
    """
    Generator that processes each chunk from the API response.
    It extracts the token, appends it to a cumulative string,
    and yields the token for further processing.
    """
    content_response = ""
    try:
        for chunk in response_text:
            if not hasattr(chunk, 'choices') or not chunk.choices:
                continue
                
            choice = chunk.choices[0]
            if not hasattr(choice, 'delta'):
                continue
                
            token = choice.delta.content
            if token:
                content_response += token
                yield token
                if delay > 0:
                    time.sleep(delay)
                            
    except Exception as e:
        print(f"Error in stream_response: {str(e)}")
        if content_response:
            yield content_response
        else:
            yield str(response_text)
       

async def process_stream(response_text,message_placeholder,delay):
    content_response = ""
    async for token in stream_response(response_text,delay):
        content_response += token
        message_placeholder.markdown(content_response + "▌")
    message_placeholder.markdown(content_response)
    return content_response    
    
