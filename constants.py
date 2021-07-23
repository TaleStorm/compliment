from datetime import time
# messages
BIRTHDAY = 'С днём рождения!'

# requests_rate
ERROR_REQUEST_RATE = 30
REQUEST_RATE = 120

# day_parts
MORNING = {
    'name': 'morning',
    'hour_start': time(7),
    'hour_end': time(12),
    'message': 'Доброе утро!'
}

DAY = {
    'name': 'day',
    'hour_start': time(12),
    'hour_end': time(18),
    'message': 'Как дела?'
}

EVENING = {
    'name': 'evening',
    'hour_start': time(18),
    'hour_end': time(22),
    'message': 'Как прошел день?'
}

NIGHT = {
    'name': 'night',
    'hour_start': time(22),
    'hour_end': time(23, 59),
    'message': 'Спокойной ночи'
}

DAY_PARTS = (
    MORNING,
    DAY,
    EVENING,
    NIGHT
)
