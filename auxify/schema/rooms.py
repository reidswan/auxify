create_room_schema = {
    "type": "object",
    "properties": {
        "room_code": {
            "type": "string"
        }
    }
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
