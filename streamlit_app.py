import os
from dotenv import load_dotenv
from src.nodes.greetings import greeting
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
from src.database.chroma_manager import ChromaManager
from src.utils.config import populate_chroma_db
from groq import Groq
import sqlite3
from streamlit import logger
from src.rag import rag
__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

app_logger = logger.get_logger("LOOP APP")
app_logger.info(f"sqlite version: {sqlite3.sqlite_version}")
app_logger.info(f"sys_version:{sys.version}")

config,prompt = load_config()
load_dotenv()

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
response_text = ""
retrieved_qa = chroma_manager.get_question_answer("Hi", 1)


if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    if "messages" not in st.session_state or st.sidebar.button("Clear conversation history"):
 
        st.session_state["messages"] = [{"role": "assistant", "content": retrieved_qa[0][0][0]}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if query := st.chat_input(placeholder="How can I help you?"):

            st.session_state.messages.append({"role": "user", "content": query})
            st.chat_message("user").write(query)
            full_response = ""
            retrieved_qa,results = chroma_manager.get_question_answer(query, 1)
            print(results)
            with st.chat_message("assistant"):
                response_text = ""
                # Stream tokens from the generate_response() function
                for chunk in st.write_stream(rag(query,retrieved_qa,groq_api_key,0.075)):
                    response_text += chunk                
                st.session_state.messages.append({"role": "assistant", "content": response_text})