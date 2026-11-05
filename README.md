# Pico LED Notification Receiver

A Raspberry Pi Pico 2 W receives notifications over WiFi and turns them into:

- an ambient glow on a 60-LED WS2812B strip behind the desk
- peripheral color cues (blue = message, green = success, red = error, ...)
- audible cues from a piezo buzzer (chirp, double beep, error tone)

The button acknowledges notifications, cycles ambient moods, and toggles the buzzer.

## Hardware

| Pico pin | Connection |
| --- | --- |
| GP0 | WS2812B DIN through a 470 ohm resistor |
| GP1 | Push button to GND (internal pull-up, active low) |
| GP2 | Piezo buzzer (passive: PWM tone, active: on/off) |
| 5V / GND | LED strip 5V supply and common ground |

The strip needs its own 5V supply. 60 LEDs at full white draw about 3.6 A.
Connect the supply ground to the Pico ground. A 3.3V data signal usually works,
but a 3.3V to 5V level shifter (for example 74AHCT125) is safer. Put a
100-1000 uF capacitor across the strip 5V/GND and keep the 470 ohm resistor
close to the first LED.

If your buzzer is passive, set `BUZZER_PASSIVE = True` in `firmware/config.py`.
If it is active, set it to `False`. A small transistor (2N2222/BC547) plus a
base resistor makes the buzzer noticeably louder than driving it from the GPIO.

## Files

```
firmware/
  main.py            startup, async loops
  config.py          pins, brightness, timings
  secrets.example.py copy to secrets.py and edit
  protocol.py        notification validation and color parsing
  led.py             ambient and notification effects
  buzzer.py          non-blocking cue player
  button.py          debounce and short/double/long press
  notifications.py   queue, priority, TTL, ambient state
  server.py          HTTP API
  wifi_manager.py    connect and reconnect
host/
  notify.py          CLI to send notifications from a PC
```

## Flash and deploy

1. Install the Pico 2 W MicroPython firmware (a recent release with WiFi support).
2. Copy the example secrets and fill in your network:

   ```bash
   cp firmware/secrets.example.py firmware/secrets.py
   ```

   Set `WIFI_SSID`, `WIFI_PASSWORD`, and a long random `API_TOKEN`
   (for example from `openssl rand -hex 16`).

3. Optionally set a static IP in `firmware/config.py`:

   ```python
   STATIC_IP = "192.168.1.50"
   STATIC_NETMASK = "255.255.255.0"
   STATIC_GATEWAY = "192.168.1.1"
   STATIC_DNS = "192.168.1.1"
   ```

   With DHCP, the IP is printed on the serial console at boot.

4. Copy the files with mpremote:

   ```bash
   pip install mpremote
   for file in main.py config.py secrets.py protocol.py led.py buzzer.py \
       button.py notifications.py server.py wifi_manager.py; do
     mpremote connect /dev/ttyACM0 fs cp "firmware/$file" ":$file"
   done
   mpremote connect /dev/ttyACM0 reset
   ```

   Replace `/dev/ttyACM0` with your port if needed. Or use Thonny's file pane
   to copy the same files to the Pico.

5. Open the serial console and note the line `WiFi: connected as <ip>`.

## Button behavior

| Gesture | Action |
| --- | --- |
| Short press | Acknowledge the current notification |
| Double press | Cycle ambient mood |
| Long press | Toggle buzzer mute |

## Ambient moods

`warm`, `cool`, `neutral`, `aurora`, `party`, `off`.

Ambient brightness defaults to `0.12`. `MAX_BRIGHTNESS = 0.5` caps every frame
to keep the strip current reasonable. Full white at 0.5 is still around 1.8 A,
so use a supply that can deliver at least 2-3 A.

## HTTP API

Every request needs this header when `API_TOKEN` is set:

```
X-API-Token: <your-token>
```

`Authorization: Bearer <your-token>` is also accepted.

### `POST /notify`

```json
{
  "type": "message",
  "color": "#3c8cff",
  "pattern": "pulse",
  "sound": "chirp",
  "priority": "normal",
  "ttl": 20,
  "label": "Build finished"
}
```

All fields are optional. `color` accepts `#RRGGBB`, `#RGB`, a `[r, g, b]` array,
or a name (`red`, `green`, `blue`, `white`, `warm`, `cool`, `cyan`, `magenta`,
`yellow`, `orange`, `purple`, `pink`, `off`).

Patterns: `solid`, `pulse`, `breathe`, `blink`, `chase`, `rainbow`.

Sounds: `none`, `chirp`, `double`, `triple`, `error`, `success`.

Priorities: `low`, `normal`, `high`. High-priority notifications preempt the
current one. Any notification with a sound repeats it until acknowledged or
until `ttl` expires: normal priorities use `SOUND_REPEAT_MS` (default 8 s) and
high priority uses `HIGH_REPEAT_MS` (default 4 s).

Default presets:

| type | color | pattern | sound | priority | ttl |
| --- | --- | --- | --- | --- | --- |
| message | blue | pulse | chirp | normal | 20 |
| meeting | purple | blink | double | high | 90 |
| success | green | pulse | success | normal | 15 |
| error | red | blink | error | high | 120 |
| warning | amber | breathe | double | normal | 30 |
| info | cyan | solid | none | low | 10 |

### `POST /ambient`

```json
{"mood": "warm", "brightness": 0.12}
```

Either field can be omitted. `mood` can be `off`.

### `POST /ack`

Acknowledges the current notification and advances the queue.

### `POST /mute`

```json
{"muted": true}
```

Omit `muted` to toggle.

### `GET /status`

Returns IP, RSSI, uptime, mute state, ambient settings, queue length, and the
current notification.

## Host CLI

Use `host/notify.py` from the PC:

```bash
export LED_HOST=192.168.1.50
export LED_TOKEN=<your-token>

python3 host/notify.py status
python3 host/notify.py notify --type success --label "Build passed"
python3 host/notify.py notify --color "#ff00aa" --pattern chase --sound triple \
  --priority high --ttl 60 --label "Deploy done"
python3 host/notify.py ambient --mood aurora --brightness 0.1
python3 host/notify.py ack
python3 host/notify.py mute --on
python3 host/notify.py demo
```

`--host` and `--token` also work directly. The CLI only uses the Python
standard library.

### curl

```bash
curl -s -X POST http://192.168.1.50/notify \
  -H "X-API-Token: $LED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"success","label":"Build passed"}'
```

### Home Assistant

```yaml
rest_command:
  pico_notify:
    url: "http://192.168.1.50/notify"
    method: POST
    headers:
      X-API-Token: !secret pico_token
      Content-Type: application/json
    payload: '{"type":"{{ type }}","label":"{{ label }}"}'
```

### Windows PowerShell

```powershell
$headers = @{ "X-API-Token" = $env:LED_TOKEN }
$body = '{"type":"message","label":"Hello"}'
Invoke-RestMethod -Method Post -Uri "http://192.168.1.50/notify" `
  -Headers $headers -ContentType "application/json" -Body $body
```

### Phone

Use HTTP Shortcuts (Android), Tasker, or MacroDroid to POST the same JSON to
`/notify`.

## Tuning

Edit `firmware/config.py`:

- `AMBIENT_BRIGHTNESS`, `NOTIFY_BRIGHTNESS`, `MAX_BRIGHTNESS`
- `AMBIENT_MOODS`, `DEFAULT_AMBIENT_MOOD`
- `SOUND_REPEAT_MS`, `HIGH_REPEAT_MS`
- `BUTTON_LONG_MS`, `BUTTON_DOUBLE_MS`
- `BUZZER_PASSIVE`, `BUZZER_VOLUME`
- `FRAME_MS` (25 ms = 40 fps)

## Troubleshooting

- **No LED output:** check 5V, common ground, DIN on GP0, and the resistor.
  This code assumes the usual WS2812B GRB colour order.
- **WiFi times out:** check 2.4 GHz network credentials. The Pico 2 W does not
  use 5 GHz networks.
- **401 Unauthorized:** send the `X-API-Token` header, or leave `API_TOKEN`
  empty in `secrets.py` to disable auth.
- **Cannot reach the IP:** set a static IP or DHCP reservation. The IP is
  printed at boot on the serial console.
- **Buzzer silent:** set `BUZZER_PASSIVE` correctly; check the pin and ground.
- **Buzzer too quiet:** drive it through a transistor.
- **Colors dim:** raise `MAX_BRIGHTNESS` and `NOTIFY_BRIGHTNESS`, but check the
  supply current first.
