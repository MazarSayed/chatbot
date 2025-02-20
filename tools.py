from src.utils.config import load_config

config,prompt = load_config()

def tools(services):
    mytools=[
        {
            "type": "function",
            "function": {
                "name": "dental_services",
                "description": "Provides information only about the following the dental services = {}".format(services),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_service": {
                            "type": "string",
                            "description": "Name of the dental service the user is inquring about"
                        },
                        "user_message": {
                            "type": "string",
                            "description": "The exact user input query, do not summarize the user input"
                        },
                        
                    },
                    "required": ["dental_service","user_message"]  # Fixed this to match the parameter name
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "general_question",
                "description": "Provides answers to general questions related to the business like insurance, parking, location, patient intake and etc ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_message": {
                            "type": "string",
                            "description": "The exact user input query, do not summarize the user input"
                        }
                    },
                    "required": ["user_message"]
                }
            }
        }
    ]
    return mytools