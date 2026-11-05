import asyncio
import time

import network

import config
import secrets


class WifiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        try:
            network.hostname("pico-led")
        except Exception:
            pass

    def is_connected(self):
        return self.wlan.isconnected()

    def ip(self):
        if not self.wlan.isconnected():
            return "0.0.0.0"
        return self.wlan.ifconfig()[0]

    def rssi(self):
        try:
            return self.wlan.status("rssi")
        except Exception:
            return None

    def apply_static_ip(self):
        if not config.STATIC_IP:
            return
        try:
            self.wlan.ifconfig(
                (
                    config.STATIC_IP,
                    config.STATIC_NETMASK,
                    config.STATIC_GATEWAY,
                    config.STATIC_DNS,
                )
            )
        except Exception as error:
            print("WiFi: static IP failed:", error)

    async def connect(self, timeout_s=20):
        if self.wlan.isconnected():
            self.apply_static_ip()
            return True
        print("WiFi: connecting to", secrets.WIFI_SSID)
        try:
            self.wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        except OSError as error:
            print("WiFi: connect error:", error)
        start = time.ticks_ms()
        while not self.wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > timeout_s * 1000:
                print("WiFi: connection timed out, status", self.wlan.status())
                try:
                    self.wlan.disconnect()
                except Exception:
                    pass
                return False
            await asyncio.sleep(0.25)
        self.apply_static_ip()
        print("WiFi: connected as", self.ip())
        return True
