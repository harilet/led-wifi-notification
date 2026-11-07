import time

import config
import protocol


class AmbientState:
    def __init__(self):
        self.moods = tuple(config.AMBIENT_MOODS)
        self.mood = config.DEFAULT_AMBIENT_MOOD
        if self.mood not in self.moods:
            self.mood = self.moods[0]
        self.brightness = config.AMBIENT_BRIGHTNESS

    def cycle(self):
        try:
            index = self.moods.index(self.mood)
        except ValueError:
            index = -1
        self.mood = self.moods[(index + 1) % len(self.moods)]
        return self.mood

    def set(self, mood=None, brightness=None):
        if mood is not None:
            if mood in self.moods or mood == "off":
                self.mood = mood
            else:
                raise ValueError("unknown mood")
        if brightness is not None:
            try:
                value = float(brightness)
            except (TypeError, ValueError):
                raise ValueError("bad brightness")
            if value < 0.0:
                value = 0.0
            if value > 1.0:
                value = 1.0
            self.brightness = value


class NotificationManager:
    def __init__(self):
        self.ambient = AmbientState()
        self.current = None
        self.queue = []
        self.muted = False
        self.next_id = 1
        self.recent_acks = []

    def enqueue(self, payload):
        note = protocol.parse_notification(payload)
        now = time.ticks_ms()
        note["id"] = self.next_id
        self.next_id += 1
        note["created"] = now
        note["started"] = now

        if note["priority"] == "high":
            if self.current is not None:
                remaining = self.remaining(self.current, now)
                if remaining > 500:
                    self.current["ttl"] = max(1, remaining // 1000)
                    self.queue.insert(0, self.current)
            self.current = note
        else:
            self.queue.append(note)
            if self.current is None:
                self.advance(now)

        self.trim_queue()
        return note["id"]

    def trim_queue(self):
        while len(self.queue) > config.MAX_QUEUE:
            drop = len(self.queue) - 1
            for index in range(len(self.queue) - 1, -1, -1):
                if self.queue[index]["priority"] != "high":
                    drop = index
                    break
            self.queue.pop(drop)

    def remaining(self, note, now):
        elapsed = time.ticks_diff(now, note["started"])
        remaining = note["ttl"] * 1000 - elapsed
        if remaining < 0:
            return 0
        return remaining

    def advance(self, now):
        if self.current is not None or not self.queue:
            return
        best = 0
        for index in range(1, len(self.queue)):
            if (
                self.queue[index]["priority"] == "high"
                and self.queue[best]["priority"] != "high"
            ):
                best = index
        note = self.queue.pop(best)
        note["started"] = now
        self.current = note

    def tick(self, now):
        if self.current is not None:
            elapsed = time.ticks_diff(now, self.current["started"])
            if elapsed >= self.current["ttl"] * 1000:
                self.current = None
        if self.current is None:
            self.advance(now)
        return self.current

    def ack(self):
        if self.current is None:
            return False
        note_id = self.current["id"]
        self.recent_acks.append(note_id)
        if len(self.recent_acks) > 16:
            self.recent_acks.pop(0)
        self.current = None
        self.advance(time.ticks_ms())
        return True

    def toggle_muted(self):
        self.muted = not self.muted
        return self.muted

    def set_muted(self, muted):
        self.muted = bool(muted)
        return self.muted

    def current_status(self):
        if self.current is None:
            return None
        note = self.current
        now = time.ticks_ms()
        return {
            "id": note["id"],
            "type": note["type"],
            "color": list(note["color"]),
            "pattern": note["pattern"],
            "sound": note["sound"],
            "priority": note["priority"],
            "ttl": note["ttl"],
            "label": note["label"],
            "elapsed_ms": time.ticks_diff(now, note["started"]),
            "remaining_ms": self.remaining(note, now),
        }
