"""
Container-specific version of the Streamlit app.
This version includes special handling for SQLite compatibility in container environments.
"""

# Try to apply SQLite fix before any other imports
try:
    import sqlite_fix
    sqlite_fix.fix_sqlite()
except Exception as e:
    print(f"Warning: Could not apply SQLite fix: {e}")

# Regular imports
import os
from dotenv import load_dotenv
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
import sqlite3
import sys
from streamlit import logger
from src.rag import rag, stream_response
import time
from src.utils.config import EmbeddingModel
from src.nodes.functions import business_info
from datetime import datetime
from groq import Groq

# Log SQLite version for debugging
print(f"SQLite version: {sqlite3.sqlite_version}")

# Load configuration and environment variables
config, prompt = load_config()
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)

# Function to initialize the system
st.set_page_config(
    page_title="Luna: helpful virtual dental concierge",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.streamlit.io/',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "# This is a Streamlit app!"
    }
)

from src.database.chroma_manager import ChromaManager
from src.utils.config import populate_chroma_db_doc
        
        # Check SQLite version compatibility
import sqlite3
sqlite_version = tuple(map(int, sqlite3.sqlite_version.split('.')))
if sqlite_version < (3, 35, 0):
    st.error(f"ChromaDB requires SQLite version >= 3.35.0, but you have {sqlite3.sqlite_version}. " 
                     "Please see container setup instructions.")
    print(f"SQLite version incompatible: {sqlite3.sqlite_version}")
else:
            # Initialize ChromaDB
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    populate_chroma_db_doc(chroma_manager)
    st.session_state["chroma_manager"] = chroma_manager
    print("ChromaDB initialized successfully.")



def clear_submit():
    st.session_state["submit"] = False



st.title("Luna: helpful virtual dental concierge")
response_text = ""
model = EmbeddingModel.get_instance()
current_service = 'None'

if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    clear_history = st.sidebar.button("Clear conversation history")

    if "messages" not in st.session_state or clear_history:
        # Get initial greeting
        response_text = """Hello! Welcome to Brookline Progressive Dental Team.\n I'm Luna, your dedicated smile concierge, here to help you find the perfect dental care just for you.\n We are a multi-specialty practice, serving the Greater Boston area for over 20 years and bringing confident smiles to thousands of families.\n Our team consists of American Board-Certified experts dedicated to providing top-tier dental care for both adults and children.\n To better assist you today, would you please first tell me what brings you here today?"""

        st.session_state["messages"] = [{"role": "assistant", "content": response_text}]
        st.session_state["chat_history"] = []
        
    # Display chat messages
    for msg in st.session_state["messages"]:
        content = msg["content"]
        st.chat_message(msg["role"]).write(content)
        print(f"\n{'='*50}\nAnswer: {content}\n{'='*50}")

    # Handle user input
    if query := st.chat_input(placeholder="How can I help you?"):
        st.session_state["messages"].append({"role": "user", "content": query})
        st.chat_message("user").write(query)

        with st.chat_message("assistant"):
            query_embedding = model.get_embedding(query)
            response_text, dental_service = rag(client, query, groq_api_key, current_service, st.session_state["messages"])
            
            if isinstance(response_text, dict):
                # Handle appointment form
                full_response = response_text
                props = full_response['data']['props']

                # Create a form in Streamlit
                with st.form(key='appointment_form'):
                    st.header(props['title'])
                    st.write(props['description'])

                    form_data = {}  # Store form data
                    # Create input fields
                    for field in props['fields']:
                        if field['type'] == 'text':
                            form_data[field['label']] = st.text_input(
                                field['label'], 
                                placeholder=field.get('placeholder', ''),
                                key=f"form_{field['label']}"
                            )
                        elif field['type'] == 'email':
                            form_data[field['label']] = st.text_input(
                                field['label'], 
                                placeholder=field.get('placeholder', ''),
                                key=f"form_{field['label']}"
                            )
                        elif field['type'] == 'tel':
                            form_data[field['label']] = st.text_input(
                                field['label'], 
                                placeholder=field.get('placeholder', ''),
                                key=f"form_{field['label']}"
                            )
                        elif field['type'] == 'date':
                            form_data[field['label']] = st.date_input(
                                field['label'],
                                key=f"form_{field['label']}"
                            )
                        elif field['type'] == 'time':
                            form_data[field['label']] = st.time_input(
                                field['label'],
                                key=f"form_{field['label']}"
                            )
                        elif field['type'] == 'textarea':
                            form_data[field['label']] = st.text_area(
                                field['label'], 
                                placeholder=field.get('placeholder', ''),
                                key=f"form_{field['label']}"
                            )

                    # Create a submit button
                    submit_button = st.form_submit_button(label=props['button']['text'])
                    
                    if submit_button:
                        # Log the form submission
                        try:
                            # Create a log entry for the form submission
                            log_entry = {
                                "type": "appointment_booking",
                                "timestamp": datetime.now().isoformat(),
                                "form_data": form_data
                            }
                            
                            # Here you would typically save this to your database
                            print("Form submission logged:", log_entry)
                            st.success("""Thank you for your request! Our team will contact you shortly to set up your appointment. 
                                       Is there anything else I can help you in the meantime?""")
                        except Exception as e:
                            st.error(f"Error booking appointment: {str(e)}")

            else:
                # Handle streaming text response
                full_response = ""
                try:
                    full_response = st.write_stream(stream_response(response_text, 0.0075))
                except Exception as e:
                    st.error(f"Error displaying response: {str(e)}")
                    
                if dental_service in config['services']:
                    current_service = dental_service    
                print("current_service:", current_service)   
                st.session_state["messages"].append({"role": "assistant", "content": full_response}) 