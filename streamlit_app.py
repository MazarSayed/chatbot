import os
from dotenv import load_dotenv
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
from src.database.chroma_manager import ChromaManager
from src.utils.config import populate_chroma_db
from groq import Groq
import sqlite3
from streamlit import logger
from src.rag import rag,stream_response
import time
import threading
import time
from src.utils.config import EmbeddingModel
from streamlit_autorefresh import st_autorefresh

#__import__('pysqlite3')
#import sys

#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

#app_logger = logger.get_logger("LOOP APP")
#app_logger.info(f"sqlite version: {sqlite3.sqlite_version}")
#app_logger.info(f"sys_version:{sys.version}")

config,prompt = load_config()
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)
chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
populate_chroma_db(chroma_manager)

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
#groq_api_key = st.text_input("Groq API Key", type="password")
response_text = ""

model = EmbeddingModel.get_instance()
query_embedding = model.get_embedding("Hi")
answers, questions = chroma_manager.general_get_qa(query_embedding, config["services"], 1)[:2]  # Only get first two return values

if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    #st_autorefresh(interval=20000, key="inactivity_autorefresh")

    clear_history = st.sidebar.button("Clear conversation history")

    if "messages" not in st.session_state or clear_history:
        # Initialize with the full answer including buttons
        initial_message = answers[0]
        st.session_state["messages"] = [{"role": "assistant", "content": initial_message}]
        st.session_state["chat_history"] = []

    #if "last_activity" not in st.session_state or clear_history:
    #    st.session_state["last_activity"] = time.time()

    # Check inactivity: if more than 20 seconds have passed without user interaction,
    # and the last message isn't already the inactivity prompt, then append the prompt.
    #if time.time() - st.session_state["last_activity"] >= 60:
    #    if not st.session_state["messages"] or st.session_state["messages"][-1]["content"] != "I understand you might be taking some time to think or research. If you have any questions, I'm here to help. When you're ready, feel free to make an appointment using this form Request for Free Consultation":
    #        st.session_state["messages"].append({
    #            "role": "assistant",
    #            "content": "I understand you might be taking some time to think or research. If you have any questions, I'm here to help. When you're ready, feel free to make an appointment using this form Request for Free Consultation"
    #        })
    #    st.session_state["last_activity"] = time.time()  # Reset timer after sending prompt

    # Display chat messages
    for msg in st.session_state["messages"]:
        content = msg["content"]
        if isinstance(content, list):
            content = content[0]
        if isinstance(content, str):
            # Remove any leading/trailing quotes and brackets if it's a string representation of a list
            if content.startswith('["') and content.endswith('"]'):
                content = content[2:-2]
        st.chat_message(msg["role"]).markdown(content)

    # Handle user input
    if query := st.chat_input(placeholder="How can I help you?"):
    #    st.session_state["last_activity"] = time.time()
        st.session_state["messages"].append({"role": "user", "content": query})
        st.chat_message("user").write(query)

        with st.chat_message("assistant"):
            query_embedding = model.get_embedding(query)
            response_text = rag(client, query, groq_api_key, st.session_state["messages"])
            full_response = ""
            for token in st.write_stream(stream_response(response_text, 0.0075)):
                full_response += token
    #    st.session_state["last_activity"] = time.time()
        #st.write(buttons)
        st.session_state["messages"].append({"role": "assistant", "content": full_response})
