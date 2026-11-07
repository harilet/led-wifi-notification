# FEATURES

Legend: `[x]` shipped, `[~]` in progress, `[ ]` idea.

## Shipped

- [x] WiFi-connected notification receiver on Pico 2 W with ambient LED and buzzer cues.
- [x] 60-LED WS2812B output on GP0, with pins configurable in `firmware/config.py`.
- [x] Ambient moods: warm, cool, neutral, aurora, party, off.
- [x] Ambient brightness runs at the global `MAX_BRIGHTNESS` cap.
- [x] Notification patterns: solid, pulse, breathe, blink, chase, rainbow.
- [x] Preset types with sensible color/pattern/sound/priority/TTL defaults.
- [x] Priority queue with high-priority preemption, TTL expiry, and bounded queue size.
- [x] Sound cues repeat until acknowledged or TTL expires.
- [x] Passive piezo PWM and active buzzer on/off support; configurable volume and mute.
- [x] Button: short press acknowledges or cycles ambient when idle; long press toggles mute.
- [x] No double-press gesture.
- [x] Public family alert page generated from `ALERT_PRESETS` and `ALERT_ORDER`.
- [x] Public preset-only `POST /alert` with cooldown; control endpoints stay token-protected.
- [x] Token-protected API: `/notify`, `/ambient`, `/ack`, `/mute`, `/status`, `/api`.
- [x] PC CLI in `host/notify.py` for status, notifications, ambient, ack, mute, demo.
- [x] WiFi connect/reconnect and optional static IP.
- [x] README with wiring, setup, API, tuning, and troubleshooting.

## In progress

- [~] On-device validation of the newest button, ambient brightness, and repeat-sound changes.
- [~] End-to-end family-page test from phones on the LAN (buttons, cooldown, dismissal).
- [~] Buzzer finalization with the PN2222A low-side driver and 5V supply.
- [~] README sync with current config values and the no-double-press behavior.

## Ideas

- [ ] Persist ambient mood, brightness, and mute state across reboots.
- [ ] Optional webhook/MQTT bridge for external automation systems.
- [ ] More family presets and easier customization flow.
- [ ] QR code or home-screen shortcut for the family alert page.
- [ ] Reverse-direction action: button press triggers an external webhook.

## Non-goals

- Home Assistant on the Pico, or any Home Assistant/MQTT/cloud dependency.
- Day/evening scheduling or focus/Pomodoro timers.
- LED matrix, text, or games; the strip is a single 60-LED line.
- A custom mobile app; the built-in web page is the family interface.
- Public internet exposure; the server is LAN-only by design.
- Per-commit documentation updates; session memory is updated at session end.
