from groq import Groq
import time
from test import chat_with_llama

def rag(query,groq_api_key,chat_history):
    
    if len(chat_history) > 10:
        recent_history = chat_history[-10:]
    else:
        recent_history = chat_history


    retrieved_answers,retrieved_questions = chat_with_llama(query,recent_history,groq_api_key) 

    Answer = "\n\n".join(retrieved_answers[0])

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "You will be shown the user's question and the exact Answer you need to provide."
                "Answer the user's question using the same format provided in the Answer with no changes."
            )
        }
    ]
    messages.extend(recent_history)

    # Create the current user message
    user_message = {
        "role": "user",
        "content": f"Question: {query}. \n Answer : {Answer}. \n"
    }
    messages.append(user_message)
    
    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")
    print(f"\n{'='*50}\n Answer : {Answer}\n{'='*50}")


    client = Groq(api_key=groq_api_key)
    content_response = ""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature = 0,
        max_tokens = 4096,
        stream = True)

    return response


def stream_response(response_text,delay):
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
    
