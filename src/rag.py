from groq import Groq
import time

def rag(query, retrieved_documents,groq_api_key,delay,chat_history=None):
    Answer = "\n\n".join(retrieved_documents[0])

    if chat_history is None:
        chat_history = []
    
    if len(chat_history) > 6:
        recent_history = chat_history[-6:]
    else:
        recent_history = chat_history
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence. "
                "Your name is Luna, you are very patient, friendly and polite. "
                "Your users will ask questions about our Dental Services and Dental Care in general. "
                "You will be shown the user's question and the exact Answer you need to provide."
                "Answer the user's question using the same format provided in the Answer with no changes."
                "If the question is not related, then Answer: 'Invalid question.' "
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

    for chunk in response:
        chunk = chunk.choices[0].delta.content
        time.sleep(delay)
        if chunk:
            content_response += chunk
            yield chunk
    assistant_message = {"role": "assistant", "content": content_response}
    chat_history.extend([user_message, assistant_message])        