from src.utils.config import load_config

config,prompt = load_config()

def tools(services,query,history):
    print(f"\n{'='*50}\n recent history: {history[-2]}\n{'='*50}")
    mytools=[
        {
            "type": "function",
            "function": {
                "name": "dental_services",
                "description": """Provides Information only regarding dental services that helps your teeth, for example - {}, if no dental service is provided do no call this function """.format(services),
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
                "description": """Provides information regarding dental services related to Insurance, parking, location, patient intake and etc """,
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