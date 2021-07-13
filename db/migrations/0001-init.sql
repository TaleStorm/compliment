CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY NOT NULL,
        username TEXT NOT NULL,
        birthday DATE NOT NULL ,
        chat_id INTEGER UNIQUE NOT NULL ,
        last_message TIME ,
        message_time TIME ,
        message_text TEXT
);

CREATE TABLE IF NOT EXISTS day_parts(
    id INTEGER PRIMARY KEY NOT NULL,
    part_name TEXT NOT NULL,
    hour_start INTEGER NOT NULL,
    hour_end INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages(
    message TEXT NOT NULL,
    day_part_id INT,
    FOREIGN KEY (day_part_id) REFERENCES day_parts(id)
);

CREATE TABLE IF NOT EXISTS birthday (
    user_id INT UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    congratulate BOOLEAN DEFAULT FALSE
)

INSERT INTO IF NOT EXISTS
    day_parts (id, part_name, hour_start, hour_end)
VALUES
    (1, 'morning', 7, 12),
    (2, 'day', 12, 18),
    (3, 'evening', 18, 22),
    (4, 'night', 22, 24);