create_room_schema = {
    "type": "object",
    "properties": {
        "room_code": {
            "type": "string"
        },
        "room_name": {
            "type": "string"
        }
    },
    "required": ["room_name"]
}

enqueue_song_schema = {
    "type": "object",
    "properties": {
        "uri": {
            "type": "string"
        }
    },
    "required": ["uri"]
}

join_room_schema = {
    "type": "object",
    "properties": {
        "room_code": {
            "type": "string"
        }
    }
}
