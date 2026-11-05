NAMED_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "warm": (255, 150, 40),
    "cool": (80, 160, 255),
    "cyan": (0, 220, 255),
    "magenta": (255, 0, 200),
    "yellow": (255, 220, 0),
    "orange": (255, 120, 0),
    "purple": (160, 60, 255),
    "pink": (255, 80, 160),
    "off": (0, 0, 0),
}

PATTERNS = ("solid", "pulse", "breathe", "blink", "chase", "rainbow")
SOUNDS = ("none", "chirp", "double", "triple", "error", "success")
PRIORITIES = ("low", "normal", "high")

TYPE_DEFAULTS = {
    "message": {
        "color": (60, 140, 255),
        "pattern": "pulse",
        "sound": "chirp",
        "priority": "normal",
        "ttl": 20,
    },
    "meeting": {
        "color": (170, 60, 255),
        "pattern": "blink",
        "sound": "double",
        "priority": "high",
        "ttl": 90,
    },
    "success": {
        "color": (0, 220, 120),
        "pattern": "pulse",
        "sound": "success",
        "priority": "normal",
        "ttl": 15,
    },
    "error": {
        "color": (255, 30, 30),
        "pattern": "blink",
        "sound": "error",
        "priority": "high",
        "ttl": 120,
    },
    "warning": {
        "color": (255, 150, 0),
        "pattern": "breathe",
        "sound": "double",
        "priority": "normal",
        "ttl": 30,
    },
    "info": {
        "color": (0, 200, 255),
        "pattern": "solid",
        "sound": "none",
        "priority": "low",
        "ttl": 10,
    },
}


def byte(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return 0
    if value < 0:
        return 0
    if value > 255:
        return 255
    return value


def parse_color(value, default):
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (byte(value[0]), byte(value[1]), byte(value[2]))
    if isinstance(value, str):
        text = value.strip().lower()
        if text in NAMED_COLORS:
            return NAMED_COLORS[text]
        if text.startswith("#"):
            text = text[1:]
        if len(text) == 3:
            try:
                return (
                    int(text[0] * 2, 16),
                    int(text[1] * 2, 16),
                    int(text[2] * 2, 16),
                )
            except ValueError:
                return default
        if len(text) == 6:
            try:
                return (
                    int(text[0:2], 16),
                    int(text[2:4], 16),
                    int(text[4:6], 16),
                )
            except ValueError:
                return default
    return default


def parse_number(value, default, minimum, maximum):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def parse_notification(payload):
    data = payload if isinstance(payload, dict) else {}

    note_type = data.get("type", "message")
    if not isinstance(note_type, str) or not note_type:
        note_type = "message"
    note_type = note_type[:32]

    base = TYPE_DEFAULTS.get(note_type, TYPE_DEFAULTS["message"])

    color = parse_color(data.get("color", base["color"]), base["color"])

    pattern = data.get("pattern", base["pattern"])
    if pattern not in PATTERNS:
        pattern = base["pattern"]

    sound = data.get("sound", base["sound"])
    if sound not in SOUNDS:
        sound = base["sound"]

    priority = data.get("priority", base["priority"])
    if priority not in PRIORITIES:
        priority = base["priority"]

    ttl = int(parse_number(data.get("ttl", base["ttl"]), base["ttl"], 1, 3600))

    label = data.get("label", "")
    if not isinstance(label, str):
        label = str(label)
    label = label[:48]

    return {
        "type": note_type,
        "color": color,
        "pattern": pattern,
        "sound": sound,
        "priority": priority,
        "ttl": ttl,
        "label": label,
    }
