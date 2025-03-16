from groq import Groq
import time
from test import chat_with_llama
import json
from src.utils.config import load_config

def rag(client, query, groq_api_key, current_service, chat_history):
    config,prompt = load_config()

    if len(chat_history) > 7:
        recent_history = chat_history[-7:]
    else:
        recent_history = chat_history[:]

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")

    answers = chat_with_llama(client, query,current_service, recent_history)
    if isinstance(answers, dict):
        dental_service = "none"
        return answers, dental_service  # Return appointment form if answer is a dict
    else :
        dental_service = answers[1]
    # Flatten the list of answers if it's a list of lists
    Context = answers[0]
    print(f"\n{'='*50}\nUser message: {answers[2]}\n{'='*50}")
    print(f"\n{'='*50}\n Context: {Context}\n{'='*50}")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Brookline Dental Team. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "Provide answers in a structured format with appropriate line breaks and bolds only when needed like virtual dental concierge"
                "Make sure to curate your response to showcase the brand of Brookline Dental Team"
                "If the user asks about the appointment form, send out the appointment form to the user as a reply"
                "Don't ask user to fill out the appointment form on every response, provide the form only when the user asks for it"
                "Here is your welcome message = {}".format(config['welcome_message'])
            )
        }
    ]
    messages.extend(recent_history)

    # Create the current user message
    user_message = {
        "role": "user",
        "content": f""" 
                    Question: {answers[2]}\n
                    Context: {Context}. \n
                    Dental_Service: {dental_service}\n

                    Follow the steps given below:\n
                        1. Using the Context provide a response only to answer the Question in 3 -4 sentences\n
                        Note: Do not provide any additional information than requrired for the Question.\n
                        2. Output your response in the structured format with appropriate line breaks and bolds only when needed like a virtual dental concierge.\n
                        3. If the answer to the Question is not in the Context and the question is regarding the dental clinic & the business:\n
                           Then provide a tattical response to keep the conversation going and ask the user to contact the front office by filling out the appointment form for more information.\n\n

                    Note: Provide very detailed 6-7 sentence answers for questions only based on treatment plan and after care for the dental services.\n
                    Provide the output by making sure you follow above steps with no additional text.\n
                    Do not provide topics in the response, but structure your response with appropriate line breaks and bolds only when needed like a virtual dental concierge.\n
                    """
    }
    messages.append(user_message)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.5,
        max_tokens=8192,
        stream=True)
    # Process the streamed response to get the complete text
    # response_text = ""
    # for chunk in response:
    #     if chunk.choices[0].delta.content:
    #         response_text += chunk.choices[0].delta.content
    #         if "<output>" in response_text and "</output>" in response_text:
    #             start = response_text.find("<output>") + len("<output>")
    #             end = response_text.find("</output>")
    #             response_text = response_text[start:end].strip()
    #             print("struct_response:",response_text)

    # try:
    #     # Parse the JSON response
    #     json_response = json.loads(response_text)
    #     # Extract status and final_answer, with fallbacks
    #     status = json_response.get("status", "")
    #     final_answer = json_response.get("final_response", "")
        
    #     # If we got a valid response, use it
    #     if status and final_answer:
    #         is_relevant = (status == "Relevant")
    #     else:
    #         # If missing required fields, treat as invalid JSON
    #         raise json.JSONDecodeError("Missing required fields", response_text, 0)
            
    # except json.JSONDecodeError as e:
    #     print(f"JSON decoding error: {e}")

    #     # If JSON parsing fails or invalid format, use original answer
    #     final_answer = json_response.split('final_response":')[1].strip().rstrip('}')
    #     is_relevant = True  # Default to showing buttons

    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     final_answer = "An unexpected error occurred."
    #     is_relevant = False  

    #print(f"\n{'='*50}\nAnswer: {response}\n{'='*50}")

    # Return the final answer and buttons based on relevance
    #final_buttons = buttons 
    #print("Final Buttons:",final_buttons)
    return response,dental_service


def stream_response(response_text, delay):
    """
    Generator that processes each chunk from the API response.
    It extracts the token, appends it to a cumulative string,
    and yields the token for further processing.
    """
    content_response = ""    
    # Check if response_text is a streaming response or a regular response
    if hasattr(response_text, '__iter__') and not isinstance(response_text, (str, dict)):
        for chunk in response_text:
            try:
                token = chunk.choices[0].delta.content
                if token:
                    content_response += token
                    yield token
                time.sleep(delay)
            except AttributeError as e:
                print(f"Error processing chunk: {e}")
                continue
    else:
        # For non-streaming responses, return the entire text at once
        content_response = str(response_text)
        yield content_response

    print(f"\n{'='*50}\nAnswer: {content_response}\n{'='*50}")
       
    
    
