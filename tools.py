
def tools():
    mytools=[
        {
            "type": "function",
            "function": {
                "name": "dental_services",
                "description": "Provides information about the different dental services of the business",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_service": {
                            "type": "string",
                            "description": "Name of the dental service the user is inquring about"
                        },
                        "query": {
                            "type": "string",
                            "description": "A detailed query of the user input query"
                        },
                        
                    },
                    "required": ["dental_service","query"]  # Fixed this to match the parameter name
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
                        "query": {
                            "type": "string",
                            "description": "A detailed query of the user input query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    return mytools