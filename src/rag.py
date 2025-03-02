from groq import Groq
import time
from test import chat_with_llama

def rag(client,query,groq_api_key,chat_history):
    
    if len(chat_history) > 6:
        recent_history = chat_history[-6:]
    else:
        recent_history = chat_history

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")

    answers,questions = chat_with_llama(client,query,recent_history) 

    Answer = "\n\n".join(answers)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "You will be given three question & answer pairs, you have find the matching QUESTION and use it's ANSWER"
                "Use the same format in the One Most Appropriate Answer"
                "If Answer not found, without using any of the answer , guide the user to fill the Appointment Request Form to be connected with practice front office"
                "Never mention the answer was not found in our database"
                "Note: Provide only the Answer"
                
            )
        }
    ]
    messages.extend(recent_history)

    # Create the current user message
    user_message = {
        "role": "user",
        "content": f""" 
                        Question 1:{questions[0]} Answer 1: {answers[0]}. \n 
                        Question 2:{questions[1]} Answer 2: {answers[1]}. \n 
                        Question 3:{questions[2]} Answer 3: {answers[2]}. \n
                        Find the Question that is most matching and Output the Answer of the Matching Question.\n
                        If Answer not found, without using any of the answer , 
                        guide the me to fill the Appointment Request Form to be connected with practice front office.\n

                        My Question: {query}
                        """
    }
    messages.append(user_message)
    
    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")
    print(f"\n{'='*50}\n Answer : {answers}\n{'='*50}")


    client = Groq(api_key=groq_api_key)

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
    
