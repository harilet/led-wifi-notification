#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


DEFAULT_HOST = os.environ.get("LED_HOST", "192.168.1.50")
DEFAULT_TOKEN = os.environ.get("LED_TOKEN", "")


def build_request(args, method, path, payload=None):
    url = "http://%s:%d%s" % (args.host, args.port, path)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    token = args.token or DEFAULT_TOKEN
    if token:
        request.add_header("X-API-Token", token)
    return request


def call(args, method, path, payload=None):
    request = build_request(args, method, path, payload)
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
            print(body)
            return json.loads(body)
    except urllib.error.HTTPError as error:
        print("HTTP %d: %s" % (error.code, error.read().decode("utf-8")))
        sys.exit(1)
    except (urllib.error.URLError, OSError) as error:
        print("Connection failed:", error)
        sys.exit(1)


def command_notify(args):
    payload = {
        "type": args.type,
        "pattern": args.pattern,
        "sound": args.sound,
        "priority": args.priority,
        "ttl": args.ttl,
        "label": args.label,
    }
    if args.color:
        payload["color"] = args.color
    call(args, "POST", "/notify", payload)


def command_ambient(args):
    payload = {}
    if args.mood:
        payload["mood"] = args.mood
    if args.brightness is not None:
        payload["brightness"] = args.brightness
    call(args, "POST", "/ambient", payload)


def command_ack(args):
    call(args, "POST", "/ack", {})


def command_mute(args):
    if args.on:
        payload = {"muted": True}
    elif args.off:
        payload = {"muted": False}
    else:
        payload = {}
    call(args, "POST", "/mute", payload)


def command_status(args):
    call(args, "GET", "/status")


def command_demo(args):
    events = [
        ("info", "#00c8ff", "solid", "none", "low", "info"),
        ("message", "#3c8cff", "pulse", "chirp", "normal", "message"),
        ("success", "#00dc78", "pulse", "success", "normal", "build passed"),
        ("warning", "#ff9600", "breathe", "double", "normal", "warning"),
        ("meeting", "#aa3cff", "blink", "double", "high", "meeting in 5 min"),
        ("error", "#ff1e1e", "blink", "error", "high", "build failed"),
    ]
    for note_type, color, pattern, sound, priority, label in events:
        payload = {
            "type": note_type,
            "color": color,
            "pattern": pattern,
            "sound": sound,
            "priority": priority,
            "ttl": 6,
            "label": label,
        }
        print("Sending", note_type, label)
        call(args, "POST", "/notify", payload)
        time.sleep(2.0)


def connection_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=argparse.SUPPRESS)
    parser.add_argument("--token", default=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=argparse.SUPPRESS)
    return parser


def main():
    parser = argparse.ArgumentParser(
        description="Control the Pico LED notifier",
        parents=[connection_parser()],
    )
    parser.set_defaults(host=DEFAULT_HOST, port=80, token="", timeout=5.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    notify = subparsers.add_parser(
        "notify", help="send a notification", parents=[connection_parser()]
    )
    notify.add_argument("--type", default="message")
    notify.add_argument("--color", default=None)
    notify.add_argument(
        "--pattern",
        default="pulse",
        choices=["solid", "pulse", "breathe", "blink", "chase", "rainbow"],
    )
    notify.add_argument(
        "--sound",
        default="chirp",
        choices=["none", "chirp", "double", "triple", "error", "success"],
    )
    notify.add_argument("--priority", default="normal", choices=["low", "normal", "high"])
    notify.add_argument("--ttl", type=int, default=20)
    notify.add_argument("--label", default="")
    notify.set_defaults(handler=command_notify)

    ambient = subparsers.add_parser(
        "ambient", help="set the idle ambient mode", parents=[connection_parser()]
    )
    ambient.add_argument(
        "--mood",
        default=None,
        choices=["warm", "cool", "neutral", "aurora", "party", "off"],
    )
    ambient.add_argument("--brightness", type=float, default=None)
    ambient.set_defaults(handler=command_ambient)

    ack = subparsers.add_parser(
        "ack", help="acknowledge the current notification", parents=[connection_parser()]
    )
    ack.set_defaults(handler=command_ack)

    mute = subparsers.add_parser(
        "mute", help="mute or unmute the buzzer", parents=[connection_parser()]
    )
    group = mute.add_mutually_exclusive_group()
    group.add_argument("--on", action="store_true")
    group.add_argument("--off", action="store_true")
    mute.set_defaults(handler=command_mute)

    status = subparsers.add_parser(
        "status", help="show device status", parents=[connection_parser()]
    )
    status.set_defaults(handler=command_status)

    demo = subparsers.add_parser(
        "demo", help="send a sequence of test notifications", parents=[connection_parser()]
    )
    demo.set_defaults(handler=command_demo)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
