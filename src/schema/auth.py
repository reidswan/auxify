register_user_schema = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": "string"
        },
        "last_name": {
            "type": "string"
        },
        "email": {
            "type": "string"
        },
        "password": {
            "type": "string"
        }
    },
    "required": ["first_name", "last_name", "email", "password"]
}

login_schema = {
    "type": "object",
    "properties": {
        "email": {
            "type": "string"
        },
        "password": {
            "type": "string"
        }
    },
    "required": ["email", "password"]
}
