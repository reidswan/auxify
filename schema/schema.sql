PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS spotify_token (
    token_id INTEGER PRIMARY KEY,
    spotify_user_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NULL DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT UNSIGNED NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (user_id),
    UNIQUE (spotify_user_id)
);
CREATE INDEX IF NOT EXISTS idx_spotify_token_created_at ON spotify_token(created_at);

CREATE TABLE IF NOT EXISTS room (
    room_id INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL, -- id of user that owns this room
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)), -- "boolean; is this room still active?"
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    room_code TEXT NULL DEFAULT NULL, -- passcode used to join a room; null for open joining
    FOREIGN KEY (owner_id) REFERENCES user (user_id)
);
CREATE INDEX IF NOT EXISTS idx_room_owner_active ON room (owner_id, active);
CREATE INDEX IF NOT EXISTS idx_room_created_at ON room (created_at);

CREATE TABLE IF NOT EXISTS room_member (
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id) REFERENCES room (room_id),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
);
