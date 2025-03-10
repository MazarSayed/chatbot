#from src.utils.config import load_config

#config,prompt = load_config()

def tools(services,query,history):
    recent_history = history[-3:-1]
    print(f"\n{'='*50}\n recent history: {recent_history}\n{'='*50}")

    mytools=[
       
        {
            "type": "function",
            "function": {
                "name": "business_info",
                "description": """Provides Information related to Brookline business information and it's dental_services such as - {}, if not in the list of dental_services, let dental_services = 'None',
                                You need to identify the dental_service and question_describtion based on user_input={} and chat_history={},
                                Do not call this function if the user wants to book an appointment.""".format(services,query,recent_history),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_service": {
                            "type": "string",
                            "description": "Name of the dental service the user is inquring about based on user_input and chat_history"
                        },
                        "question_describtion": {
                            "type": "string",
                            "description": "Provide a question_describtion based on user_input and chat_history"
                        },
                        
                    },
                    "required": ["dental_service","question_describtion"] 
                }
            }
        },
         {
            "type": "function",
            "function": {
                "name": "book_appointment",
                "description": """call this function to Book an appointment or consultation with the Brookline Dental Team""",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
    ]
    return mytools