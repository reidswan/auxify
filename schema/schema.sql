USE auxify;

CREATE TABLE IF NOT EXISTS `user` (
    `user_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(100) NOT NULL,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `password_hash` VARCHAR(100) NOT NULL,
    UNIQUE KEY (`email`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `spotify_token` (
    `token_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `spotify_user_id` VARCHAR(255) NOT NULL,
    `access_token` VARCHAR(255) NOT NULL,
    `refresh_token` VARCHAR(255) NULL DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT NOW(),
    `duration_seconds` INT UNSIGNED NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`),
    INDEX `index_created_at` (`created_at`),
    UNIQUE KEY (`spotify_user_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `room` (
    `room_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `owner` BIGINT UNSIGNED NOT NULL COMMENT "id of user that owns this room",
    `active` TINYINT(1) UNSIGNED NOT NULL DEFAULT 1 COMMENT "boolean; is this room still active?",
    `created_at` TIMESTAMP NOT NULL DEFAULT NOW(),
    `room_code` VARCHAR(50) NULL DEFAULT NULL COMMENT "passcode used to join a room; null for open joining", -- storing this in plaintext is an acceptable security 'flaw', as it will be displayed clearly on the room display screen
    FOREIGN KEY (`owner`) REFERENCES `user` (`user_id`),
    INDEX `index_owner_active` (`owner`, `active`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `room_member` (
    `room_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (`room_id`, `user_id`),
    FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`),
    FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB;


