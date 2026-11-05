import math
import time

import machine
import neopixel

import config


def build_gamma():
    return [int((value / 255.0) ** 2.2 * 255.0 + 0.5) for value in range(256)]


GAMMA = build_gamma()


def lerp(first, second, factor):
    if factor < 0.0:
        factor = 0.0
    if factor > 1.0:
        factor = 1.0
    return (
        int(first[0] + (second[0] - first[0]) * factor),
        int(first[1] + (second[1] - first[1]) * factor),
        int(first[2] + (second[2] - first[2]) * factor),
    )


def scale_color(color, scale):
    if scale <= 0.0:
        return (0, 0, 0)
    if scale > 1.0:
        scale = 1.0
    red = int(GAMMA[color[0]] * scale)
    green = int(GAMMA[color[1]] * scale)
    blue = int(GAMMA[color[2]] * scale)
    return (
        red if red < 255 else 255,
        green if green < 255 else 255,
        blue if blue < 255 else 255,
    )


def hsv_to_rgb(hue, saturation, value):
    if saturation <= 0.0:
        channel = int(value * 255)
        return (channel, channel, channel)
    hue = (hue % 1.0) * 6.0
    sector = int(hue)
    fraction = hue - sector
    p = value * (1.0 - saturation)
    q = value * (1.0 - saturation * fraction)
    t = value * (1.0 - saturation * (1.0 - fraction))
    if sector == 0:
        rgb = (value, t, p)
    elif sector == 1:
        rgb = (q, value, p)
    elif sector == 2:
        rgb = (p, value, t)
    elif sector == 3:
        rgb = (p, q, value)
    elif sector == 4:
        rgb = (t, p, value)
    else:
        rgb = (value, p, q)
    return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


MOOD_COLORS = {
    "warm": ((255, 90, 20), (255, 190, 90)),
    "cool": ((20, 60, 255), (120, 200, 255)),
    "neutral": ((255, 225, 190), (255, 245, 225)),
    "aurora": ((0, 180, 140), (60, 80, 255)),
}


class LedStrip:
    def __init__(self):
        self.count = config.LED_COUNT
        self.strip = neopixel.NeoPixel(machine.Pin(config.LED_PIN), self.count)
        self.off()

    def off(self):
        self.strip.fill((0, 0, 0))
        self.strip.write()

    def fill(self, color, scale):
        value = scale_color(color, scale)
        for index in range(self.count):
            self.strip[index] = value
        self.strip.write()

    def render_ambient(self, now, mood, brightness):
        scale = min(config.MAX_BRIGHTNESS, brightness)
        if scale <= 0.0 or mood == "off":
            self.fill((0, 0, 0), 0.0)
            return

        seconds = now / 1000.0

        if mood == "party":
            for index in range(self.count):
                hue = (index / float(self.count) + seconds * 0.05) % 1.0
                self.strip[index] = scale_color(hsv_to_rgb(hue, 1.0, 1.0), scale)
            self.strip.write()
            return

        if mood == "neutral":
            breathe = 0.85 + 0.15 * math.sin(seconds * 0.6)
            self.fill(MOOD_COLORS["neutral"][0], scale * breathe)
            return

        colors = MOOD_COLORS.get(mood, MOOD_COLORS["warm"])
        first, second = colors
        for index in range(self.count):
            position = (index / float(self.count - 1) + seconds * 0.03) % 1.0
            mix = 0.5 + 0.5 * math.sin(2.0 * math.pi * position)
            color = lerp(first, second, mix)
            breathe = 0.85 + 0.15 * math.sin(seconds * 0.5)
            self.strip[index] = scale_color(color, scale * breathe)
        self.strip.write()

    def render_notification(self, now, note):
        elapsed = time.ticks_diff(now, note["started"]) / 1000.0
        base_scale = min(config.MAX_BRIGHTNESS, config.NOTIFY_BRIGHTNESS)
        color = note["color"]
        pattern = note["pattern"]

        if pattern == "pulse":
            factor = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(2.0 * math.pi * elapsed / 1.2))
            self.fill(color, base_scale * factor)
        elif pattern == "breathe":
            factor = 0.08 + 0.92 * (0.5 - 0.5 * math.cos(2.0 * math.pi * elapsed / 3.0))
            self.fill(color, base_scale * factor)
        elif pattern == "blink":
            on = (elapsed % 0.6) < 0.3
            self.fill(color, base_scale if on else 0.0)
        elif pattern == "chase":
            head = int(elapsed * 35.0) % (self.count + 8)
            for index in range(self.count):
                distance = head - index
                if 0 <= distance < 8:
                    tail = 1.0 - distance / 8.0
                    self.strip[index] = scale_color(color, base_scale * (0.25 + 0.75 * tail))
                else:
                    self.strip[index] = scale_color(color, base_scale * 0.06)
            self.strip.write()
        elif pattern == "rainbow":
            for index in range(self.count):
                hue = (index / float(self.count) + elapsed * 0.35) % 1.0
                self.strip[index] = scale_color(hsv_to_rgb(hue, 1.0, 1.0), base_scale)
            self.strip.write()
        else:
            self.fill(color, base_scale)
