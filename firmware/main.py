import asyncio
import gc
import time

import config

try:
    import secrets
except ImportError:
    raise SystemExit(
        "Missing secrets.py. Copy secrets.example.py to secrets.py and edit it."
    )

from button import Button
from buzzer import Buzzer
from led import LedStrip
from notifications import NotificationManager
from server import HttpServer
from wifi_manager import WifiManager


async def led_loop(led, notifier, buzzer):
    last_sound_id = None
    last_sound_ms = 0
    while True:
        now = time.ticks_ms()
        current = notifier.tick(now)

        if current is None:
            if last_sound_id is not None:
                buzzer.stop()
                last_sound_id = None
            led.render_ambient(now, notifier.ambient.mood, notifier.ambient.brightness)
        else:
            led.render_notification(now, current)
            if current["id"] != last_sound_id:
                last_sound_id = current["id"]
                last_sound_ms = now
                if current["sound"] != "none":
                    buzzer.play(current["sound"])
            elif current["sound"] != "none":
                if current["priority"] == "high":
                    repeat_ms = config.HIGH_REPEAT_MS
                else:
                    repeat_ms = config.SOUND_REPEAT_MS
                if time.ticks_diff(now, last_sound_ms) >= repeat_ms:
                    buzzer.play(current["sound"])
                    last_sound_ms = now

        buzzer.tick(now)
        await asyncio.sleep(config.FRAME_MS / 1000.0)


async def button_loop(button, notifier, buzzer):
    while True:
        event = button.poll(time.ticks_ms())
        if event == "single":
            if notifier.current is None:
                notifier.ambient.cycle()
            elif notifier.ack():
                buzzer.stop()
        elif event == "long":
            muted = notifier.toggle_muted()
            buzzer.set_muted(muted)
            if not muted:
                buzzer.play("chirp")
        await asyncio.sleep(0.02)


async def network_loop(wifi, server):
    while True:
        if not wifi.is_connected():
            await wifi.connect()
        if wifi.is_connected() and not server.started:
            try:
                await server.start()
            except Exception as error:
                print("HTTP: failed to start:", error)
        await asyncio.sleep(5)


async def main():
    print("Pico LED notifier booting")
    gc.collect()

    led = LedStrip()
    buzzer = Buzzer()
    button = Button()
    notifier = NotificationManager()
    buzzer.set_muted(notifier.muted)
    wifi = WifiManager()
    server = HttpServer(notifier, wifi, buzzer, secrets.API_TOKEN)

    led.render_ambient(
        time.ticks_ms(), notifier.ambient.mood, notifier.ambient.brightness
    )

    await asyncio.gather(
        led_loop(led, notifier, buzzer),
        button_loop(button, notifier, buzzer),
        network_loop(wifi, server),
    )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Stopped")
