LED_PIN = 0
LED_COUNT = 60
BUTTON_PIN = 1
BUZZER_PIN = 2

BUZZER_PASSIVE = True
BUZZER_VOLUME = 1.0

MAX_BRIGHTNESS = 0.5
AMBIENT_BRIGHTNESS = 0.12
NOTIFY_BRIGHTNESS = 0.45

AMBIENT_MOODS = ("warm", "cool", "neutral", "aurora", "party")
DEFAULT_AMBIENT_MOOD = "warm"

ALERT_COOLDOWN_MS = 2000
ALERT_ORDER = ("call", "dinner", "come", "help")

ALERT_PRESETS = {
    "call": {
        "type": "meeting",
        "label": "Please call me",
        "color": "#aa3cff",
        "pattern": "blink",
        "sound": "triple",
        "priority": "high",
        "ttl": 180,
    },
    "dinner": {
        "type": "success",
        "label": "Dinner is ready",
        "color": "#00dc78",
        "pattern": "pulse",
        "sound": "success",
        "priority": "high",
        "ttl": 120,
    },
    "come": {
        "type": "message",
        "label": "Come here",
        "color": "#3c8cff",
        "pattern": "chase",
        "sound": "double",
        "priority": "high",
        "ttl": 120,
    },
    "help": {
        "type": "error",
        "label": "Help needed",
        "color": "#ff1e1e",
        "pattern": "blink",
        "sound": "error",
        "priority": "high",
        "ttl": 300,
    },
}

FRAME_MS = 25
SOUND_REPEAT_MS = 1000
HIGH_REPEAT_MS = 1000
MAX_QUEUE = 16

BUTTON_DEBOUNCE_MS = 25
BUTTON_LONG_MS = 700
BUTTON_DOUBLE_MS = 350

HTTP_PORT = 80

STATIC_IP = "192.168.1.56"
STATIC_NETMASK = "255.255.255.0"
STATIC_GATEWAY = "192.168.1.1"
STATIC_DNS = "192.168.1.1"
