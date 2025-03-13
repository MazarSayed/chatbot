from groq import Groq
import time
from test import chat_with_llama, calculate_ceiling_tokens
import json
from src.utils.config import load_config
from src.storage.containers.logs import LogsContainer
from src.handlers.logging_handler import LLMLoggingHandler
import tiktoken

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

async def rag(client, query, groq_api_key, current_service, chat_history, logs_container=None, user_id=None):
    config, prompt = load_config()
    
    # Initialize logging handler if we have container and user_id
    logging_handler = None
    if logs_container and user_id:
        logging_handler = LLMLoggingHandler(logs_container.sqlite_manager, user_id)

    if len(chat_history) > 7:
        recent_history = chat_history[-7:]
    else:
        recent_history = chat_history[:]

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")


    # Get response from chat_with_llama with token tracking
    Context, dental_service, token_usage = chat_with_llama(client, query, current_service, recent_history, logging_handler=logging_handler)

    # Unpack result with token usage
    if isinstance(Context, dict):
        # Handle appointment form case
        if logs_container and user_id:
            await logs_container.create_conversation_log(
                user_id=user_id,
                input_text=query,
                output_text="book_appointment",
                input_tokens=token_usage["input_tokens"],
                output_tokens=token_usage["output_tokens"],
                model_name="llama3-70b-8192"
            )
        return Context, dental_service

    # Handle business info case
    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")
    print(f"\n{'='*50}\n Context: {Context}\n{'='*50}")
    
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
                    My_Question: {query}\n
                    Context: {Context}. \n
                    dental_service: {dental_service}

                    Follow the steps given below:
                        1. Analyze My_Question and Context given above.
                        2. Provide a brief response to answer My_Question using the Context mainly.
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

    # Accumulate streaming response and count tokens
    output_text = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            output_text += chunk.choices[0].delta.content

    # Count output tokens and ceiling to nearest 1000
    chat_output_tokens = calculate_ceiling_tokens(count_tokens(output_text))
    chat_input_tokens = calculate_ceiling_tokens(count_tokens(str(messages)))

    # Add up all token usage
    total_input_tokens = calculate_ceiling_tokens(token_usage["input_tokens"] + chat_input_tokens)
    total_output_tokens = calculate_ceiling_tokens(token_usage["output_tokens"] + chat_output_tokens)

    if logs_container and user_id:
        await logs_container.create_conversation_log(
            user_id=user_id,
            input_text=query,
            output_text=output_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            model_name="llama3-70b-8192"
        )

    return response,dental_service    

def stream_response(response_text, delay):
    """
    Generator that processes each chunk from the API response.
    It extracts the token, appends it to a cumulative string,
    and yields the token for further processing.
    """
    content_response = ""    
    for chunk in response_text:
        if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
            token = chunk.choices[0].delta.content
            if token:
                content_response += token
                yield token
                time.sleep(delay)
    
    print(f"\n{'='*50}\nAnswer: {content_response}\n{'='*50}")
       
    
    
