import asyncio
import json
import time

import config


REASONS = {
    200: "OK",
    202: "Accepted",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    413: "Payload Too Large",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
}


class HttpServer:
    def __init__(self, notifier, wifi, buzzer, token):
        self.notifier = notifier
        self.wifi = wifi
        self.buzzer = buzzer
        self.token = token
        self.started = False
        self.server = None
        self.started_ms = time.ticks_ms()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle, "0.0.0.0", config.HTTP_PORT
        )
        self.started = True
        print("HTTP: listening on", self.wifi.ip(), "port", config.HTTP_PORT)

    async def handle(self, reader, writer):
        try:
            await self.serve(reader, writer)
        except Exception as error:
            print("HTTP: handler error:", error)
            try:
                await self.send(writer, 500, {"ok": False, "error": "internal"})
            except Exception:
                pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def serve(self, reader, writer):
        request_line = await reader.readline()
        if not request_line:
            return

        try:
            parts = request_line.decode().strip().split()
            method = parts[0]
            path = parts[1]
        except Exception:
            await self.send(writer, 400, {"ok": False, "error": "bad request"})
            return

        if "?" in path:
            path = path.split("?", 1)[0]

        headers = {}
        header_bytes = 0
        while True:
            line = await reader.readline()
            if not line:
                break
            header_bytes += len(line)
            if header_bytes > 4096:
                await self.send(
                    writer, 431, {"ok": False, "error": "headers too large"}
                )
                return
            if line in (b"\r\n", b"\n"):
                break
            try:
                key, value = line.decode().split(":", 1)
                headers[key.strip().lower()] = value.strip()
            except Exception:
                pass

        if not self.authorized(headers):
            await self.send(writer, 401, {"ok": False, "error": "unauthorized"})
            return

        try:
            length = int(headers.get("content-length", "0") or 0)
        except ValueError:
            length = 0
        if length > 2048:
            await self.send(writer, 413, {"ok": False, "error": "payload too large"})
            return

        body = b""
        while len(body) < length:
            chunk = await reader.read(length - len(body))
            if not chunk:
                break
            body += chunk

        if method == "GET" and path == "/":
            await self.send(
                writer,
                200,
                {
                    "ok": True,
                    "name": "pico-led-notifier",
                    "endpoints": [
                        "GET /status",
                        "POST /notify",
                        "POST /ambient",
                        "POST /ack",
                        "POST /mute",
                    ],
                },
            )
        elif method == "GET" and path == "/status":
            await self.send(writer, 200, self.status())
        elif method == "POST" and path == "/notify":
            data = self.parse_body(body)
            if data is None:
                await self.send(writer, 400, {"ok": False, "error": "invalid json"})
                return
            note_id = self.notifier.enqueue(data)
            await self.send(writer, 202, {"ok": True, "id": note_id})
        elif method == "POST" and path == "/ambient":
            data = self.parse_body(body)
            if data is None:
                await self.send(writer, 400, {"ok": False, "error": "invalid json"})
                return
            try:
                self.notifier.ambient.set(
                    data.get("mood"), data.get("brightness")
                )
            except ValueError as error:
                await self.send(writer, 400, {"ok": False, "error": str(error)})
                return
            await self.send(
                writer,
                200,
                {
                    "ok": True,
                    "ambient": {
                        "mood": self.notifier.ambient.mood,
                        "brightness": self.notifier.ambient.brightness,
                    },
                },
            )
        elif method == "POST" and path == "/ack":
            acked = self.notifier.ack()
            await self.send(writer, 200, {"ok": True, "acked": acked})
        elif method == "POST" and path == "/mute":
            data = self.parse_body(body)
            if data is None:
                await self.send(writer, 400, {"ok": False, "error": "invalid json"})
                return
            if "muted" in data:
                muted = self.notifier.set_muted(data["muted"])
            else:
                muted = self.notifier.toggle_muted()
            self.buzzer.set_muted(muted)
            await self.send(writer, 200, {"ok": True, "muted": muted})
        else:
            await self.send(writer, 404, {"ok": False, "error": "not found"})

    def parse_body(self, body):
        if not body:
            return {}
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def authorized(self, headers):
        if not self.token:
            return True
        supplied = headers.get("x-api-token", "")
        if not supplied:
            authorization = headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                supplied = authorization[7:].strip()
        return supplied == self.token

    def status(self):
        now = time.ticks_ms()
        ambient = self.notifier.ambient
        return {
            "ok": True,
            "ip": self.wifi.ip(),
            "rssi": self.wifi.rssi(),
            "uptime_s": time.ticks_diff(now, self.started_ms) // 1000,
            "muted": self.notifier.muted,
            "ambient": {
                "mood": ambient.mood,
                "brightness": ambient.brightness,
            },
            "queue": len(self.notifier.queue),
            "current": self.notifier.current_status(),
        }

    async def send(self, writer, status, payload):
        body = json.dumps(payload).encode()
        reason = REASONS.get(status, "OK")
        try:
            writer.write(
                ("HTTP/1.1 %d %s\r\n" % (status, reason)).encode()
            )
            writer.write(b"Content-Type: application/json\r\n")
            writer.write(("Content-Length: %d\r\n" % len(body)).encode())
            writer.write(b"Connection: close\r\n\r\n")
            writer.write(body)
            await writer.drain()
        except Exception:
            pass
