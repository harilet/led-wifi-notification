# SCRATCH

Append dated entries, keep top current, prune what is obvious from code.

## Current focus

- Bench-validate the latest firmware: single-press ambient cycling, notification
  acknowledgement, max ambient brightness, repeated buzzer until dismiss/TTL.
- Verify the family alert page from real phones on the LAN, including the sender's
  "Acknowledged" confirmation when the physical button dismisses the alert.
- Finish the buzzer chain with the PN2222A low-side driver.

## Next up

1. Upload the uncommitted firmware changes (`button.py`, `main.py`, `config.py`) and reset.
2. Test idle single press (cycles ambient), active single press (acknowledges), long press
   (mute), and confirm the buzzer stops on dismissal.
3. Open `http://192.168.1.56/` from two phones; send each preset; check the 2 s cooldown.
4. Send an alert from a phone, dismiss it with the physical button, and confirm the page
   changes to "Acknowledged. Thank you!".
5. Confirm current draw at `MAX_BRIGHTNESS = 0.8` is safe for the 5V supply.
6. Sync README with actual config values and button behavior.
7. Commit the tested firmware changes.

## Known issues / watch-outs

- README drift: it still says `MAX_BRIGHTNESS = 0.5`, repeat intervals 8 s/4 s, and
  "double press" in the file list. Current config is `MAX_BRIGHTNESS = 0.8`,
  `SOUND_REPEAT_MS = 1000`, `HIGH_REPEAT_MS = 1000`.
- `host/notify.py` defaults to `192.168.1.50`; `STATIC_IP` is `192.168.1.56`. Set
  `LED_HOST` or pass `--host`.
- Hardware behavior is not fully verified; syntax checks and ad-hoc stubbed tests only.
- Family-page acknowledgement is poll-based (1.5 s); closing the page ends feedback.
- No automated tests, CI, formatter, or lint script exist.
- `MAX_BRIGHTNESS = 0.8` can exceed 2 A; full white on 60 LEDs is still much higher.
- Buzzer must match `BUZZER_PASSIVE`; check common ground and the transistor pinout.
- `mpremote` is only in the local `base/` venv, not on the global PATH.
- `firmware/secrets.py` is local and gitignored; do not commit it.
- `GET /` and `POST /alert` are public by design; control endpoints require the token.
- Queue overflow drops non-high notifications.

## Decisions

- 2026-11-07 — Family notifications: use a Pico-hosted web page (`GET /`, `POST /alert`)
  instead of Home Assistant, a cloud service, or a custom app; lowest setup cost.
- 2026-11-07 — Alert security: keep `/` and `/alert` public, make `/alert` preset-only
  with a 2 s cooldown, and keep the rest token-protected.
- 2026-11-07 — Sender feedback: add public read-only `/alert/status` and poll it from the
  family page; confirmed dismissals return `acknowledged`, no token or push channel needed.
- 2026-11-07 — Button mapping: short press acknowledges an active notification or cycles
  ambient when idle; long press toggles mute; double press removed.
- 2026-11-07 — Brightness: ambient requests 1.0 but is capped by `MAX_BRIGHTNESS`;
  current cap is 0.8 for output vs. current tradeoff.
- 2026-11-07 — Notification sound: repeat the cue until acknowledgement or TTL; current
  normal and high intervals are both 1000 ms.
- 2026-11-07 — Buzzer drive: PN2222A low-side switch, 1 kΩ base resistor, 5 V supply,
  common ground; flyback diode for magnetic buzzers.
- 2026-11-07 — Session memory: AGENTS.md is the map; FEATURES.md is scope; SCRATCH.md is
  working memory; update at session end, not per commit.

## Session log

### 2026-11-07 — Family-page acknowledgement feedback

- Added per-boot IDs and recent-ack tracking; `POST /alert` returns `id` and `boot`.
- Added public read-only `GET /alert/status?boot=&id=` returning `active`, `pending`,
  `acknowledged`, or `ended`.
- Updated `webui.py` to poll every 1.5 s and show active/queued/acknowledged/ended.
- Verified with `py_compile`, stubbed HTTP tests, ack-history tests, and `node --check`
  on the extracted JavaScript; hardware phone test pending.

### 2026-11-07 — Session memory flow

- Added `AGENTS.md`, `docs/FEATURES.md`, `docs/SCRATCH.md`.
- Inspected repo structure, README, firmware modules, host CLI, git state, and tooling.
- Verified `python3 -m py_compile firmware/*.py host/notify.py` (OK),
  `python3 host/notify.py --help` (OK), and `base/bin/mpremote --help` (OK).
- No app code changed.

### 2026-11-07 — Latest firmware tweaks (uncommitted at session start)

- Button: single press now acknowledges or cycles ambient when idle; double-press removed.
- Ambient: requests full brightness (`AMBIENT_BRIGHTNESS = 1.0`), capped at `MAX_BRIGHTNESS = 0.8`.
- Buzzer: repeat intervals set to 1000 ms; static IP set to `192.168.1.56`.
- Verified with `py_compile` and ad-hoc stubbed button/buzzer tests; hardware pending.

### 2026-11-07 — Family alert web page (`22abad5`)

- Added `firmware/webui.py`; public `GET /` and preset-only `POST /alert`; presets,
  order, cooldown, and a generated mobile page.
- Removed the Home Assistant example/docs afterward.
- Verified with `py_compile` and ad-hoc stubbed HTTP tests; phone test pending.

### 2026-11-07 — Initial receiver (`94a6df3`)

- Added firmware modules, HTTP API, LED/buzzer/button handling, and `host/notify.py`.
- Verified with `py_compile` and ad-hoc module tests; one buzzer beep confirmed on hardware.
