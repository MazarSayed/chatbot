#from src.utils.config import load_config
from google.genai import types


#config,prompt = load_config()

def tools_calling(services, query, history, current_service):
    """Create function declarations for the Gemini API"""
    recent_history = history[-3:-1] if len(history) >= 3 else history
    print(f"\n{'='*50}\n recent history: {recent_history}\n{'='*50}")

    # Define the business_info function schema
    business_info_schema = {
        "type": "OBJECT",
        "properties": {
            "dental_service": {
                "type": "STRING",
                "description": "Name of the dental service the user is inquiring about based on user_input and chat_history"
            },
            "question_description": {
                "type": "STRING",
                "description": "Provide a question_description based on user_input and chat_history"
            },
            "previous_dental_service": {
                "type": "STRING",
                "description": f"previous_dental_service = {current_service}"
            }    
        },
        "required": ["dental_service", "question_description", "previous_dental_service"] 
    }

    # Define the book_appointment function schema
    book_appointment_schema = {
        "type": "OBJECT",
        "properties": {
            "request": {
                "type": "STRING",
                "description": "request for booking the appointment"
            }
        },
        "required": ["request"]
    }

    # Create function declarations
    business_info_func = {
        "name": "business_info",
        "description": f"""Provides Information related to Brookline business information, to make a payment and it's dental_services such as - {services}.
                      If not in the list of dental_services, let dental_service = 'None'.
                      You need to identify the dental_service and question_description based on user_input and chat_history.
                      Do not call this function if the user wants to book an appointment.""",
        "parameters": business_info_schema
    }

    book_appointment_func = {
        "name": "book_appointment",
        "description": "Call this function only if the user requests to Book an appointment or consultation with the Brookline Dental Team",
        "parameters": book_appointment_schema
    }

    # Create a list of tools following Google Generative AI SDK format
    tools = [
        {
            "function_declarations": [business_info_func, book_appointment_func]
        }
    ]

    return tools