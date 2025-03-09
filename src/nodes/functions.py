from src.utils.config import load_config
from src.database.chroma_manager import ChromaManager
from typing_extensions import Annotated
import os
from src.utils.config import EmbeddingModel

def business_info(dental_service: str,question_describtion:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(os.path.abspath(config['chroma_path']))
    model = EmbeddingModel.get_instance()
    query_embedding = model.get_embedding(question_describtion)
    dental_service = dental_service.lower()
    #current_service = None

    if dental_service in config["services"]:
        current_service = dental_service
        answers = chroma_manager.get_doc(query_embedding,dental_service,2)
    elif dental_service == 'none':
        answers = chroma_manager.get_doc(query_embedding,dental_service,2)
        current_service = ''
    else:
        current_service = ''
        answers = [[f"""Thank you for considering us for your dental needs! Unfortunately, 
            we do not currently offer {dental_service}. However, our dentists have an excellent network of specialists in this specialty. 
            We recommend coming in for a personalized assessment so our dentist can refer you to the right expert for your needs. 
            Would you like to schedule a consultation?"""]]
    #    questions = [[f"Services not in the list of {dental_service}"]]
#    buttons = [[{}]]  # Empty buttons for services not in the list
    return [answers,current_service]

def book_appointment()->str:
    print("Booking appointment...")
    appointment_widget = {
        "status": "success",
        "data": {
            "component": "AppointmentWidget",
            "props": {
                "title": "Schedule Your Appointment",
                "description": "Fill out the form below to book your appointment.",
                "fields": [
                    {
                        "label": "Name",
                        "type": "text",
                        "placeholder": "Enter your name",
                        "required": True
                    },
                    {
                        "label": "Email",
                        "type": "email",
                        "placeholder": "Enter your email",
                        "required": True
                    },
                    {
                        "label": "Phone Number",
                        "type": "tel",
                        "placeholder": "Enter your phone number",
                        "required": True
                    },
                    {
                        "label": "Preferred Date",
                        "type": "date",
                        "required": True
                    },
                    {
                        "label": "Preferred Time",
                        "type": "time",
                        "required": True
                    },
                    {
                        "label": "Additional Notes",
                        "type": "textarea",
                        "placeholder": "Any additional information or requests"
                    }
                ],
                "button": {
                    "text": "Book Appointment",
                    "style": {
                        "backgroundColor": "#007BFF",
                        "color": "white",
                        "padding": "12px 24px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                },
                "widgetStyle": {
                    "border": "1px solid #ccc",
                    "borderRadius": "8px",
                    "padding": "20px",
                    "boxShadow": "0 2px 10px rgba(0, 0, 0, 0.1)",
                    "backgroundColor": "#f9f9f9"
                }
            },
            "message": "Appointment widget component created successfully."
        }
    }
    dental_service = 'none'
    return dict(appointment_widget)
