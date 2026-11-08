# AGENTS.md

## New session checklist

1. Read this file.
2. Read `docs/FEATURES.md` for scope.
3. Read `docs/SCRATCH.md` for current focus, decisions, and known issues.
4. Run `git status`; app changes may be uncommitted.
5. Make only the requested change; avoid unrelated refactors.
6. After finishing work, update `docs/FEATURES.md` and `docs/SCRATCH.md`.

This is a MicroPython Pico 2 W project plus a Python host CLI. There is no Flutter/Dart
`pubspec` or `lib/` directory.

## Verified commands

Run from the repo root.

| Purpose | Command |
| --- | --- |
| Syntax check | `python3 -m py_compile firmware/*.py host/notify.py` |
| Host CLI help | `python3 host/notify.py --help` |
| Local mpremote help | `base/bin/mpremote --help` |
| Serial REPL | `base/bin/mpremote connect /dev/ttyACM0 repl` |
| Reset device | `base/bin/mpremote connect /dev/ttyACM0 reset` |
| List serial ports | `base/bin/mpremote devs` |

Deploy from this repo (replace the port if needed):

```bash
for file in main.py config.py secrets.py protocol.py led.py buzzer.py \
    button.py notifications.py server.py webui.py wifi_manager.py; do
  base/bin/mpremote connect /dev/ttyACM0 fs cp "firmware/$file" ":$file"
done
base/bin/mpremote connect /dev/ttyACM0 reset
```

Device-only CLI examples (Pico must be reachable; token from `firmware/secrets.py`):

```bash
LED_HOST=192.168.1.56 LED_TOKEN=... python3 host/notify.py status
python3 host/notify.py notify --type success --label "Build passed"
python3 host/notify.py demo
```

Tooling facts:

- No build or package script; firmware is uploaded to the Pico.
- No test suite, CI, formatter, or separate lint script exists.
- `py_compile` checks syntax only; it does not import MicroPython modules or test hardware.
- `mpremote` is not on the global PATH here; use `base/bin/mpremote` or activate `base/`.

## Architecture map

- `firmware/main.py` — boot, asyncio LED/buzzer loop, button loop, WiFi/server loop.
- `firmware/config.py` — pins, brightness, timing, ambient moods, alert presets/order/cooldown, static IP.
- `firmware/secrets.example.py` — template for `secrets.py` (WiFi credentials and API token).
- `firmware/protocol.py` — notification defaults, validation, color parsing.
- `firmware/notifications.py` — ambient state, priority queue, TTL, preemption, mute, status.
- `firmware/led.py` — gamma/HSV helpers, ambient and notification effects.
- `firmware/buzzer.py` — non-blocking cue sequences; passive PWM or active on/off.
- `firmware/button.py` — debounce and short/long press detection.
- `firmware/server.py` — HTTP server, token auth, routes, public family page, alert send/status.
- `firmware/webui.py` — generates the family alert page from presets and order; polls alert status.
- `firmware/wifi_manager.py` — WiFi connect, optional static IP, connection reporting.
- `host/notify.py` — standard-library CLI for the REST API.
- `README.md` — wiring, setup, API, tuning, troubleshooting. May lag behind code.
- `base/` — local gitignored Python venv containing `mpremote`; not app code.
- `docs/` — session memory (`FEATURES.md`, `SCRATCH.md`).
- `.gitignore` — excludes `firmware/secrets.py`, bytecode, `.venv/`, `/base`.

## Runtime data and storage

- No flash or database persistence; runtime state resets on reboot.
- `firmware/secrets.py` (gitignored): `WIFI_SSID`, `WIFI_PASSWORD`, `API_TOKEN`.
- `config.ALERT_PRESETS`: key → `{type, label, color, pattern, sound, priority, ttl}`.
- `config.ALERT_ORDER`: family-page button order.
- In-memory state: ambient `{mood, brightness}`, current notification and queue, `muted`,
  `last_alert_ms`, recent acknowledged IDs, and a per-boot ID.
- Notification objects include `id`, `type`, `color`, `pattern`, `sound`, `priority`, `ttl`,
  `label`, `created`, `started`.
- HTTP payloads: `/notify` JSON object, `/alert` `{"preset": "<key>"}`, `/ambient`
  `{"mood": "...", "brightness": 0..1}`, `/mute` `{"muted": bool}`.
- Family-page polling: `GET /alert/status?boot=<boot>&id=<id>` returns `active`, `pending`,
  `acknowledged`, or `ended`; it is read-only and public.

## Product rules and non-negotiables

- Target is Pico 2 W + MicroPython; keep code non-blocking and use `time.ticks_diff`.
- Default pins: GP0 LED, GP1 button, GP2 buzzer. Keep them configurable in `config.py`.
- The product is an ambient desk glow plus peripheral color and audible cues.
- Notification semantics: high priority preempts; sounds repeat until acknowledged or TTL;
  short press acknowledges an active notification, or cycles ambient when idle; long press
  toggles mute. There is no double-press gesture.
- Security boundary: `GET /`, `POST /alert`, and `GET /alert/status` are intentionally public;
  `/alert` is preset-only and rate-limited, and `/alert/status` is read-only. All other
  endpoints require the token when `API_TOKEN` is set. Do not make `/notify` public.
- The family page must stay generated from `ALERT_PRESETS`/`ALERT_ORDER`; do not hardcode buttons.
- `MAX_BRIGHTNESS` caps every LED frame; ambient requests full brightness but stays capped.
  Do not raise the cap without considering 5V supply current.
- Do not introduce a Home Assistant, MQTT, or cloud dependency; LAN HTTP is the chosen path.
- Keep the public/authorized route split, preset validation, and alert cooldown intact.

## Gotchas

- 60 WS2812B LEDs at full white draw about 3.6 A. Use an external 5V supply, common ground,
  a 470 ohm data resistor, and a bulk capacitor. 3.3V data may need level shifting.
- Intermittent uniform wrong colors or flicker are usually connection integrity, not code:
  a marginal solder joint or connector latches corrupted frames. Check and resolder the
  5V/GND/data joints before changing code or adding a shifter (2026-11-08 lesson).
- WiFi is 2.4 GHz only. Static IP is currently configured; a DHCP reservation also works.
- Warm reset can skip the static IP: if the WiFi chip stays associated across a reset,
  `network_loop` never calls `connect()`, so `apply_static_ip()` never runs and the device
  comes up on DHCP (observed 192.168.1.14) instead of `STATIC_IP`. If `.56` is unreachable,
  check the actual IP on the serial console before debugging.
- `BUZZER_PASSIVE` must match the hardware. For a PN2222A/2N2222 low-side driver: emitter to
  GND, base through 1 kΩ to GP2, collector to buzzer negative, buzzer positive to 5V. Add a
  flyback diode for a magnetic buzzer.
- WiFi is 2.4 GHz only. Static IP is currently configured; a DHCP reservation also works.
- `README.md` has drifted from current code: it still mentions old brightness/repeat values
  and "double press" in the file list. Trust `firmware/config.py` and the source.
- `host/notify.py` defaults to `192.168.1.50`; current `STATIC_IP` is `192.168.1.56`. Set
  `LED_HOST` or pass `--host`.
- `firmware/secrets.py` is local and gitignored; never commit it.
- The HTTP server is plain HTTP on port 80, intended for the local network.
- The notification queue is capped; non-high items are dropped when full.
- MicroPython lacks many CPython conveniences; avoid adding CPython-only dependencies.

## After finishing work

Update `docs/FEATURES.md` (move shipped items, prune stale ideas) and `docs/SCRATCH.md`
(current focus, decisions, session log). Update these at the end of a session, not per commit.
