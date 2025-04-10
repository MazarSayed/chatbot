from groq import Groq
import time
from test import chat_with_llama
import json
from src.utils.config import load_config
import google.genai as genai
from google.genai.types import GenerateContentConfig

def rag(client, config, query, groq_api_key, current_service, chat_history):
    """RAG pipeline for handling queries and generating responses"""
    # Limit chat history to recent messages
    if len(chat_history) > 5:
        recent_history = chat_history[-5:]
    else:
        recent_history = chat_history[:]

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")

    # Get answers from the llama function
    answers = chat_with_llama(client, config, query, current_service, recent_history)
    
    # Handle appointment form case
    if isinstance(answers, dict):
        dental_service = "none"
        return answers, dental_service
    else:
        # Extract context and dental service
        context = answers[0]
        dental_service = answers[1]
        user_message = answers[2]
    
    print(f"\n{'='*50}\nUser message: {user_message}\n{'='*50}")
    print(f"\n{'='*50}\n Context: {context}\n{'='*50}")

    system_instruction = """
                You are a helpful virtual dental concierge for a Dental Care Website specifically owned by Brookline Progressive Dental Team. 
                Your name is Luna, you are very patient, friendly and polite. 
                You will be given user questions related to our Dental Services, Doctors profiles and Dental Care in general.
                Provide answers in a structured format with appropriate line breaks and bolds.
                Provides max 2-3 sentences for all questionsa except for questions about treatment plans/procedures provide 6-7 detailed sentences asnwer.
                If the user asks about the appointment form, send out the appointment form to the user as a reply.
                Focus on past user queries and answer pairs to provide more relevant answers accordingly.
                Please don't mention that you're using the context information. Just provide a natural, helpful response.
                Keep your introduction or response to Hi short and concise."""
                
    
    # Create a properly structured prompt for Gemini
    prompt_text = f"""        
        INFORMATION : {context}\n\n
        
        DENTAL SERVICE: {dental_service}\n\n

        Please provide a helpful response that:\n
        1. Directly answers the user's question using the information\n
        2. Use a friendly, professional tone and behave like a dental concierge assistant\n
        3. Structures your response with appropriate paragraphs and formatting and keep your response concise and to the point \n
        4. If the context doesn't contain the answer, politely suggest contacting the front office for more information\n\n

        USER QUESTION: {user_message}\n\n

        Keep your response concise and to the point and answers the USER QUESTION.\n
        Please don't mention that you're using the INFORMATION, Just provide a natural, helpful response.\n"""
        
    print(f"\n{'='*50}\nRecent history: {recent_history}\n{'='*50}")

    # Create a new prompt message to add to history
    prompt_message = {
        "role": "user",
        "parts": [{"text": prompt_text}]
    }
    
    # Create a copy of recent_history to avoid modifying the original
    formatted_messages = recent_history.copy()
    # Add the new prompt
    formatted_messages.append(prompt_message)

    try:
        generation_config = GenerateContentConfig(
            system_instruction=system_instruction,
        )
        # Use the client's models API to generate content with proper formatting
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=formatted_messages,
            config=generation_config
        )
        
        # Return the response with proper text extraction
        return response, dental_service
    
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        if "404" in str(e):
            print("Model not found. Please check the model name and try again.")
        # Return a simple string error message that can be displayed
        error_response = "I'm having trouble generating a response right now. Please try again later."
        return error_response, dental_service


def stream_response(response_text, delay=0):
    """Process responses from Gemini API with simulated streaming"""
    content_response = ""
    
    # Handle string responses (like error messages)
    if isinstance(response_text, str):
        yield response_text
        return
        
    # Handle Gemini response object
    try:
        # If response has a text attribute, extract it
        if hasattr(response_text, 'text'):
            text = response_text.text
            # Simulate streaming by yielding character by character
            for char in text:
                content_response += char
                yield char
                time.sleep(delay)
        # If it's iterable (for actual streaming responses if supported later)
        elif hasattr(response_text, '__iter__'):
            for chunk in response_text:
                # Handle chunk.text format
                if hasattr(chunk, 'text'):
                    token = chunk.text
                    if token:
                        content_response += token
                        yield token
                        time.sleep(delay)
                # Handle parts format
                elif hasattr(chunk, 'parts'):
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            content_response += part.text
                            yield part.text
                            time.sleep(delay)
                # Fallback for other formats
                else:
                    chunk_str = str(chunk)
                    if chunk_str:
                        content_response += chunk_str
                        yield chunk_str
                        time.sleep(delay)
        # For any other response format, convert to string and simulate streaming
        else:
            response_string = str(response_text)
            for char in response_string:
                content_response += char
                yield char
                time.sleep(delay)
    except Exception as e:
        print(f"Error in stream_response: {str(e)}")
        error_msg = f"Error streaming response: {str(e)}"
        yield error_msg
        content_response += error_msg
    
    print(f"\n{'='*50}\nAnswer: {content_response}\n{'='*50}")
       
    
    

def ask_gemini(client, query, context="", model="gemini-2.0-flash"):
    """
    Generates a response from Google's Gemini model.
    """
    try:
        print(f"\nQuestion: {query}")
        
        # If context is provided, include it in the prompt with proper format
        if context:
            prompt = {
                "role": "user", 
                "parts": [{
                    "text": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context provided:"
                }]
            }
        else:
            prompt = {
                "role": "user", 
                "parts": [{
                    "text": f"Question: {query}\n\nAnswer:"
                }]
            }
        
        # Generate response from the model without streaming
        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt]
            )
            return response
        except Exception as e:
            if "Model not found" in str(e):
                print(f"Model {model} not found, falling back to gemini-1.5-pro")
                response = client.models.generate_content(
                    model="gemini-1.5-pro",
                    contents=[prompt]
                )
                return response
            else:
                raise e
            
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return f"Sorry, I couldn't process your request: {str(e)}"
       
    
    
