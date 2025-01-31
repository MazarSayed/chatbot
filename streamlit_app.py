import os
from dotenv import load_dotenv
from src.nodes.greetings import greeting
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
from test import chat_with_llama

config,prompt = load_config()


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
groq_api_key = st.text_input("Groq API Key", type="password")
if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    Greeting = greeting(groq_api_key)

    if "messages" not in st.session_state or st.sidebar.button("Clear conversation history"):
        st.session_state["messages"] = [{"role": "assistant", "content": Greeting}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if query := st.chat_input(placeholder="How can I help you?"):

            st.session_state.messages.append({"role": "user", "content": query})
            st.chat_message("user").write(query)
            full_response = ""
            with st.chat_message("assistant"):
                for chunk in st.write_stream(chat_with_llama(query,groq_api_key)):
                    full_response += chunk
    
            
                st.session_state.messages.append({"role": "assistant", "content": full_response})





