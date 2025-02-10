import os
from dotenv import load_dotenv
from src.nodes.greetings import greeting
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
from src.database.chroma_manager import ChromaManager
from src.utils.config import populate_chroma_db
from groq import Groq
import json
import time
config,prompt = load_config()
load_dotenv()



def rag(query, retrieved_documents,groq_api_key,delay):
    information = "\n\n".join(retrieved_documents)

    messages = [
        {
            "role": "system",
            "content": """You are a helpful virtual dental concierge for a Dental Care Website owned by Loop Intelligence\n
                          Your name is Luna, you are very patient, friendly and polite. Your users are asking questions about information about Dental Service Information.
                          You will be shown the user's question, and the exact response you need to provide. Answer the user's question by that exact response with no changes."""
        },
        {"role": "user", "content": f"Question: {query}. \n Information: {information}, JSON_Response:"}
    ]
    
    print(f"\n{'='*50}\nUser message: {query}\n{'='*50}")

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
    messages.append(content_response)         
        





def clear_submit():
      st.session_state["submit"] = False


# Function to initialize the system
st.set_page_config(
        page_title="Luna: helpful virtual dental concierge",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'https://www.streamlit.io/',
            'Report a bug': "https://github.com/streamlit/streamlit/issues",
            'About': "# This is a Streamlit app!"}
        )  

st.title("Luna: helpful virtual dental concierge")
chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))

populate_chroma_db(chroma_manager)
groq_api_key = st.text_input("Groq API Key", type="password")

if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    response_text = ""
    retrieved_qa = chroma_manager.get_question_answer("Hi", 1)
    for token in rag("Hi",retrieved_qa,groq_api_key,0):
        response_text += token                

    if "messages" not in st.session_state or st.sidebar.button("Clear conversation history"):
        st.session_state["messages"] = [{"role": "assistant", "content": response_text}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if query := st.chat_input(placeholder="How can I help you?"):

            st.session_state.messages.append({"role": "user", "content": query})
            st.chat_message("user").write(query)
            full_response = ""
            retrieved_qa = chroma_manager.get_question_answer(query, 1)
            with st.chat_message("assistant"):
                response_text = ""
                # Stream tokens from the generate_response() function
                for chunk in st.write_stream(rag(query,retrieved_qa,groq_api_key,0.075)):
                    response_text += token                
                st.session_state.messages.append({"role": "assistant", "content": response_text})