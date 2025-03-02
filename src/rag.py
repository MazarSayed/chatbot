from groq import Groq
import time
from test import chat_with_llama

def rag(client,query,groq_api_key,chat_history):
    
    if len(chat_history) > 7:
        recent_history = chat_history[-7:-1]
    else:
        recent_history = chat_history[:]

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")

    answers,questions = chat_with_llama(client,query,recent_history)
    # Ensure exactly 3 items in each list
    answers = [ans[0] if isinstance(ans, list) else ans for ans in answers]
    answers = (answers + [''] * 3)[:3]
    questions = (questions + [''] * 3)[:3]

    Answer = "\n\n".join(answers)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "You will be given three quesyion and answers pairs, find most matching question and use it's answer as the most appropriate an answer"
                "Use the same format as given , it may include links and etc."
                "If the Answer is not relevant to My_Question, do not provide that answer, Instead generate an APPROPRIATE answer to My_Question and guide the user to fill the Appointment Request Form to be connected with practice front office"
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
                    Chat_History = {recent_history}    
                    Question 1: {questions[0]} Answer 1: {answers[0]}. \n
                    Question 2: {questions[1]} Answer 2: {answers[1]}. \n
                    Question 3: {questions[2]} Answer 3: {answers[2]}. \n
                    My_Question: {query}\n

                    Follow the steps given below:
                        1. Find the Question which is most similar to the My_Question, and use it's answer as the most appropriate answer based on the Chat_History .\n
                           Provide only the Answer in the same mardkdown format as given, do not make any changes to the answer.\n\n

                        2. Analzye My_Question, selected Answer from step 1 and Chat_History.\n\n
                        3. If the selected Answer is not relevant to My_Question, DO NOT provide that answer.\n\n
                        4. Instead generate an  APPROPRIATE answer to My_Question and guide the user to fill the Appointment Request Form to be connected with practice front office.\n\n
                    Do not use any preamble or postambles, just provide the answer.\n
                    Make sure to follow the steps given above.\n
                    Output:
                        """
    }
    messages.append(user_message)
    
    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")
    print(f"\n{'='*50}\n Answer : {Answer}\n{'='*50}")

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature = 0,
        max_tokens = 4096,
        stream = True)
    return response


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
    
    
