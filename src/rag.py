from groq import Groq
import time
from test import chat_with_llama
import json

def rag(client, query, groq_api_key, chat_history):
    if len(chat_history) > 4:
        recent_history = chat_history[-3:]
    else:
        recent_history = chat_history[:]

    print(f"\n{'='*50}\n all_history: {recent_history}\n{'='*50}")

    answers, questions, buttons = chat_with_llama(client, query, recent_history)
    
    # Ensure we have strings, not nested lists
    if isinstance(answers, list):
        if answers and isinstance(answers[0], list):
            answers = answers[0]
    answers = [str(ans) for ans in (answers if isinstance(answers, list) else [answers])]
    questions = [str(q) for q in (questions if isinstance(questions, list) else [questions])]
    buttons = buttons

    Answer = "\n\n".join(answers)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "Use the same format as given in Answers , it may include links and etc."
                "If the Answer is not relevant to My_Question by anyway, do not provide that Answer, Instead generate an DETAILED answer to My_Question and guide the user to fill the Appointment Request Form to be connected with practice front office"
                "Never mention the answer was not found in our database"
                "Note: Provide only the Answer in the same format"
            )
        }
    ]
    messages.extend(recent_history)

    # Create the current user message
    user_message = {
        "role": "user",
        "content": f""" 
                    My_Question: {query}\n
                    Answer: {answers[0]}. \n

                    Follow the steps given below:
                        1. Analyze My_Question and Answer given above.
                        2. Output your response in the following JSON format:
                        <output>
                            {{
                                "status": "[Relevant/Not Relevant]",
                                "final_answer": "[The answer text]"
                            }}
                        </output>    
                        
                        If Answer is relevant to My_Question:
                        - Set status as "Relevant"
                        - Use the provided Answer exactly as is, preserving allformatting and links
                        
                        If Answer is not relevant to My_Question:
                        - Set status as "Not Relevant"
                        - Generate an appropriate answer that addresses the question
                        - Include guidance about scheduling a consultation
                        - Format your response similar to our other answers with proper markdown

                    Provide only the JSON output with no additional text.
                    
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
    response_text = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            response_text += chunk.choices[0].delta.content
            if "<output>" in response_text and "</output>" in response_text:
                start = response_text.find("<output>") + len("<output>")
                end = response_text.find("</output>")
                filtered_response = response_text[start:end].strip()

    try:
        # Parse the JSON response
        filtered_response = json.loads(filtered_response)
        # Extract status and final_answer, with fallbacks
        status = filtered_response.get("status", "")
        final_answer = filtered_response.get("final_answer", "")
        
        # If we got a valid response, use it
        if status and final_answer:
            is_relevant = (status == "Relevant")
        else:
            # If missing required fields, treat as invalid JSON
            raise json.JSONDecodeError("Missing required fields", response_text, 0)
            
    except json.JSONDecodeError:
        # If JSON parsing fails or invalid format, use original answer
        final_answer = answers[0]
        is_relevant = True  # Default to showing buttons

    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")
    print(f"\n{'='*50}\nAnswer: {filtered_response}\n{'='*50}")

    # Return the final answer and buttons based on relevance
    final_buttons = buttons 
    print("Final Buttons:",final_buttons)
    return final_answer, final_buttons


def stream_response(response_text, delay):
    """
    Generator that processes each chunk from the API response.
    It extracts the token, appends it to a cumulative string,
    and yields the token for further processing.
    """
    if isinstance(response_text, str):
        words = response_text.split()
        for word in words:
            time.sleep(delay)
            yield word + " "
    else:
        content_response = ""    
        for chunk in response_text:
            token = chunk.choices[0].delta.content
            time.sleep(delay)
            if token:
                content_response += token
                yield token
    
    
