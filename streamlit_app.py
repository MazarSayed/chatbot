import os
from dotenv import load_dotenv
from src.utils.config import load_config
import streamlit as st
from langchain_groq import ChatGroq
from src.database.chroma_manager import ChromaManager
from src.utils.config import populate_chroma_db,populate_chroma_db_doc
from groq import Groq
import sqlite3
from streamlit import logger
from src.rag import rag,stream_response
import time
import threading
import time
from src.utils.config import EmbeddingModel
from streamlit_autorefresh import st_autorefresh
from src.nodes.functions import business_info
from datetime import datetime

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
populate_chroma_db_doc(chroma_manager)

# Check if initialization has already been done
#if "initialized" not in st.session_state or st.session_state["initialized"] is None:
#    st.session_state["initialized"] = True
#    #populate_chroma_db(chroma_manager)


#print("initialized:",  st.session_state["initialized"] )

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
current_service = 'None' 
if not groq_api_key:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    clear_history = st.sidebar.button("Clear conversation history")

    if "messages" not in st.session_state or clear_history:
        # Get initial greeting
        #response_text, final_buttons = rag(client, "Hi", groq_api_key, [])
               # Set default greeting if no answer is found
        response_text = """Hello! Welcome to Brookline Progressive Dental Team.\n I'm Luna, your dedicated smile concierge, here to help you find the perfect dental care just for you.\n We are a multi-specialty practice, serving the Greater Boston area for over 20 years and bringing confident smiles to thousands of families.\n Our team consists of American Board-Certified experts dedicated to providing top-tier dental care for both adults and children.\n Tobetter assist you today, would you please first tell me what brings you here today?"""

        st.session_state["messages"] = [{"role": "assistant", "content": response_text}]
        st.session_state["chat_history"] = []
        #st.session_state["buttons"] = [final_buttons]
        
        # Print buttons in the frontend

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
        st.chat_message(msg["role"]).write(content)
        print(f"\n{'='*50}\nAnswer: {content}\n{'='*50}")

        #st.write(btn)   # Print the final answer in the frontend after it is generated

    # Handle user input
    if query := st.chat_input(placeholder="How can I help you?"):
    #    st.session_state["last_activity"] = time.time()
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
                    # Create input fields based on the fields defined in the widget
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


       