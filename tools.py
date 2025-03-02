from src.utils.config import load_config

config,prompt = load_config()

def tools(services,query,history):
    print(f"\n{'='*50}\n recent history: {history[-2]}\n{'='*50}")
    mytools=[
        {
            "type": "function",
            "function": {
                "name": "dental_services",
                "description": """Provides Information only regarding dental services = {} and similar dental services which helps the teeth""".format(services),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_service": {
                            "type": "string",
                            "description": "Name of the dental service the user is inquring about"
                        },
                        "user_query": {
                            "type": "string",
                            "description": "user_query = {} ".format(query)
                        },
                        
                    },
                    "required": ["dental_service","user_query"] 
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "general_question",
                "description": """Provides infromation regarding general dental services like parking, location, etc""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "user_query = {} ".format(query)
                        }
                    },
                    "required": ["user_query"]
                }
            }
        }
    ]
    return mytools