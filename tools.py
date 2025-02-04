
def tools():
    mytools=[
        {
            "type": "function",
            "function": {
                "name": "service_testimonial",
                "description": "Provides information about the dental services of the business with customer testimonials",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dental_services": {
                            "type": "string",
                            "description": "Name of the dental service"
                        }
                    },
                    "required": ["dental_services"]  # Fixed this to match the parameter name
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "insurance_inquiry",
                "description": "Provides information about the insurance details on dental services",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "services": {
                            "type": "string",
                            "description": "Type of the dental service"
                        },
                        "insurance": {
                            "type": "string",
                            "description": "Name of the insurance"
                        }
                    },
                    "required": ["insurance"]  # Updated required fields
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "service_costing",
                "description": "Provides information about the cost of dental services",
            }
        },
        {
            "type": "function",
            "function": {
                "name": "general_question",
                "description": "Provides answers to general questions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Any question related to the Dental Practice or any questions which doesn't suit other tools"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    return mytools