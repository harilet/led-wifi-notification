import time

import machine

import config


class Button:
    def __init__(self):
        self.pin = machine.Pin(
            config.BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP
        )
        self.raw = False
        self.stable = False
        self.raw_change = time.ticks_ms()
        self.press_start = 0

    def poll(self, now):
        pressed = not self.pin.value()
        if pressed != self.raw:
            self.raw = pressed
            self.raw_change = now

        if (
            time.ticks_diff(now, self.raw_change) >= config.BUTTON_DEBOUNCE_MS
            and self.stable != self.raw
        ):
            self.stable = self.raw
            if self.stable:
                self.press_start = now
            else:
                duration = time.ticks_diff(now, self.press_start)
                if duration >= config.BUTTON_LONG_MS:
                    return "long"
                return "single"

        return None
