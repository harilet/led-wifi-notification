# SCRATCH

Append dated entries, keep top current, prune what is obvious from code.

## Current focus

- Watch the resoldered strip: confirm the random wrong-color flicker is gone and
  ambient/alert colors render correctly (warm should read orange, red alerts red).
- Sanity-check the reattached buzzer (the flicker was never a buzzer issue; it was
  reattached after the reset).
- Verify the family alert page from real phones on the LAN, including the sender's
  "Acknowledged" confirmation when the physical button dismisses the alert.

## Next up

1. Watch the strip for a day after the resolder; if random wrong colors return, recheck
   the solder joints and consider a 74AHCT125 shifter before touching code.
2. Test the buzzer: `LED_HOST=192.168.1.56 LED_TOKEN=... python3 host/notify.py notify
   --type message --label "buzzer test"`, then ack with the button or the CLI.
3. Open `http://192.168.1.56/` from two phones; send each preset; check the 2 s cooldown
   and the physical-button acknowledgement feedback.
4. Fix the warm-reset path so the static IP is applied even when WiFi stays associated.
5. Sync remaining README drift: ambient brightness claim (README says 1.0, config is
   0.5), repeat intervals (README says 8 s/4 s, config is 1000/1000 ms), and "double
   press" in the file list.

## Known issues / watch-outs

- Intermittent wrong colors RESOLVED (2026-11-08): root cause was bad solder joints on
  the strip connections, not the 3.3V data level, WiFi, or firmware. Resoldered and
  stable. If it recurs, check connections first.
- Warm reset can skip the static IP: if the WiFi chip stays associated across reset,
  `network_loop` never calls `connect()`, so `apply_static_ip()` never runs and the
  device comes up on DHCP (observed 192.168.1.14) instead of `STATIC_IP`. If `.56` is
  unreachable, check the actual IP or hard-reset before debugging.
- README drift: it claims ambient brightness defaults to 1.0 (config: 0.5), repeat
  intervals 8 s/4 s (config: 1000/1000 ms), and "double press" in the file list.
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

- 2026-11-08 — Flicker/wrong-color root cause: bad solder joints at the strip
  connections; resoldered and stable. Earlier theories (WiFi noise, 3.3V data level,
  RGB-ordered strip) were corruption artifacts from the flaky connection; the strip is a
  standard GRB WS2812B and the stock code is correct.
- 2026-11-08 — Codebase reset to `93b52a1` as the known-good baseline; all session code
  changes (buzzer removal, `LED_ORDER` experiment, doc edits) were discarded and the
  device re-synced. The buzzer was reattached; the removal is cancelled.
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

### 2026-11-08 — Flicker hunt, root cause, and reset

- Investigated intermittent wrong colors on random LEDs: exonerated the render code
  (deterministic), then WiFi (flicker persisted with a no-WiFi test build), then
  channel order (a greenish latch during a solid test led to an RGB-order theory and an
  `LED_ORDER` fix — later shown to be a corruption artifact).
- User found the real cause: bad solder joints at the strip connections; resoldered.
  A/B tests used: no-WiFi ambient loop, single-write solid latch, slow color cycle.
- Verified along the way: the buzzer-free build ran correctly on-device
  (notify/ack/status over HTTP), and `machine.bitstream` exists on this build
  (MicroPython v1.28.0) if an IRQ-atomic write is ever needed.
- Found: warm reset skips `apply_static_ip()` when WiFi stays associated (device came
  up on DHCP 192.168.1.14); documented in gotchas, not fixed.
- User reset the working tree to `93b52a1` and re-synced the device, discarding all
  session code changes. Device verified via HTTP at 192.168.1.56 afterwards.

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
