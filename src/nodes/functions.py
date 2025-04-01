from src.utils.config import load_config
from src.database.chroma_manager import ChromaManager
from typing_extensions import Annotated
import os
from src.utils.config import EmbeddingModel

def business_info(dental_service: str,question_description:str,previous_dental_service:str)->str:
    config,prompt = load_config()
    chroma_manager = ChromaManager(config)
    model = EmbeddingModel.get_instance()
    previous_dental_service = previous_dental_service.lower()
    #service_question = question_description+"-"+previous_dental_service
    print(f"\n{'='*50}\n question_description: {question_description}\n{'='*50}")
    query_embedding = model.get_embedding(question_description)
    dental_service = dental_service.lower()
    
    #current_service = None

    if dental_service !='none':
        if dental_service in config['services']:
            current_service = dental_service
        else:
            current_service = ''
        answers = chroma_manager.get_doc(query_embedding,dental_service,3)
    elif dental_service == 'none':
        answers = chroma_manager.get_doc(query_embedding,dental_service,3)
        current_service = ''
    #else:
    #    current_service = ''
    #    answers = [[f"""Thank you for considering us for your dental needs! Unfortunately, 
    #        we do not currently offer {dental_service}. However, our dentists have an excellent network of specialists in this specialty. 
    #        We recommend coming in for a personalized assessment so our dentist can refer you to the right expert for your needs. 
    #        Would you like to schedule a consultation?"""]]
    #    questions = [[f"Services not in the list of {dental_service}"]]
#    buttons = [[{}]]  # Empty buttons for services not in the list
    return [answers,current_service,question_description]

def book_appointment(user_message: str) -> dict:
    print(f"Booking appointment with context: {user_message}")
    appointment_widget = {
        "status": "success",
        "data": {
            "component": "AppointmentWidget",
            "props": {
                "title": "Schedule Your Appointment",
                "description": "Fill out the form below to book your appointment.",
                "fields": [
                    {
                        "label": "First Name",
                        "type": "text",
                        "placeholder": "Enter your first name",
                        "required": True,
                        "key": "name"
                    },
                    {
                        "label": "Last Name",
                        "type": "text",
                        "placeholder": "Enter your last name",
                        "required": True,
                        "key": "last_name"
                    },
                    {
                        "label": "Email",
                        "type": "email",
                        "placeholder": "Enter your email",
                        "required": True,
                        "key": "email"
                    },
                    {
                        "label": "Phone Number",
                        "type": "tel",
                        "placeholder": "Enter your phone number",
                        "required": True,
                        "key": "phone"
                    },
                    {
                        "label": "Patient Type",
                        "type": "radio",
                        "options": [
                            {"label": "New Patient", "value": "new"},
                            {"label": "Existing Patient", "value": "existing"}
                        ],
                        "required": True,
                        "key": "patient_type"
                    },
                    {
                        "label": "Preferred Days",
                        "type": "select",
                        "multiple": True,
                        "options": [
                            {"label": "Monday", "value": "monday"},
                            {"label": "Tuesday", "value": "tuesday"},
                            {"label": "Wednesday", "value": "wednesday"},
                            {"label": "Thursday", "value": "thursday"},
                            {"label": "Friday", "value": "friday"},
                            {"label": "Saturday", "value": "saturday"},
                            {"label": "Sunday", "value": "sunday"}
                        ],
                        "required": True,
                        "key": "preferred_days"
                    },
                    {
                        "label": "Preferred Time",
                        "type": "select",
                        "options": [
                            {"label": "AM", "value": "am"},
                            {"label": "PM", "value": "pm"}
                        ],
                        "required": True,
                        "key": "preferred_time"
                    },
                    {
                        "label": "Interested Services",
                        "type": "select",
                        "multiple": True,
                        "options": [
                            {"label": "Invisalign", "value": "invisalign"},
                            {"label": "Teeth Cleaning", "value": "teeth_cleaning"},
                            {"label": "Dental Checkup", "value": "dental_checkup"},
                            {"label": "Emergency Dental Care", "value": "emergency_dental_care"},
                            {"label": "Dental Implants", "value": "dental_implants"},
                            {"label": "Laser Treatment", "value": "laser_treatment"},
                            {"label": "Sealants", "value": "sealants"},
                            {"label": "Fluoride Treatment", "value": "fluoride_treatment"}
                        ],
                        "required": True,
                        "key": "interested_services"
                    },
                    {
                        "label": "Additional Notes",
                        "type": "textarea",
                        "placeholder": "Any additional information or requests",
                        "key": "notes"
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
    return appointment_widget
