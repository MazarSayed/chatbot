from src.utils.config import load_config

config,prompt = load_config()

def tools(services,query,history):
    print(f"\n{'='*50}\n recent history: {history[-2:-1]}\n{'='*50}")

    mytools=[
        {
            "type": "function",
            "function": {
                "name": "dental_services",
                "description": """Provides Information only regarding dental services = {} and similar dental services which helps the teeth, dental services doesn't cover anything like Insurance, parking, location etc.""".format(services),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_service": {
                            "type": "string",
                            "description": "Name of the dental service the user is inquring about"
                        },
                        "question_describtion": {
                            "type": "string",
                            "description": "Provide a detailed question_describtion based mainly based on user_query and also consider the chat_history"
                        },
                        
                    },
                    "required": ["dental_service","question_describtion"] 
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "general_question",
                "description": """Provides information regarding to the business like insurance, parking, location etc. """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question_describtion": {
                            "type": "string",
                            "description": "Provide a detailed question_describtion based mainly based on user_query and also consider the chat_history"
                        },
                    },
                    "required": ["question_describtion"]
                }
            }
        }
    ]
    return mytools