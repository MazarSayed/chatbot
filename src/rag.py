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
        return answers  # Return appointment form if answer is a dict
    
    # Flatten the list of answers if it's a list of lists
    Context = answers[0]
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

    # Create the current user message
    user_message = {
        "role": "user",
        "content": f""" 
                    My_Question: {query}\n
                    Context: {Context}. \n

                    Follow the steps given below:
                        1. Analyze My_Question and Context given above.
                        2. Provide a brief response to answer My_Question using the Context mainly.
                        3. Output your short response in the structured format with appropriate line breaks and bolds only when needed.

                    Note: Provide very detailed long answers for questions only on treatment plan and after care for the dental services
                    Provide only the output by following above steps with no additional text.
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
    print(f"\n{'='*50}\nAnswer: {response}\n{'='*50}")
    return response,answers[1]


def stream_response(response_text, delay):
    """
    Generator that processes each chunk from the API response.
    It extracts the token, appends it to a cumulative string,
    and yields the token for further processing.
    """
    content_response = ""    
    for chunk in response_text:
            token = chunk.choices[0].delta.content
            time.sleep(delay)
            if token:
                content_response += token
                yield token
    print(f"\n{'='*50}\nAnswer: {content_response}\n{'='*50}")
       
    
    
