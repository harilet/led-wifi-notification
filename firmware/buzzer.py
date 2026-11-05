import time

import machine

import config


CUES = {
    "none": [],
    "chirp": [(2200, 90)],
    "double": [(2400, 70), (0, 60), (2400, 70)],
    "triple": [(2400, 60), (0, 50), (2400, 60), (0, 50), (2400, 60)],
    "error": [(600, 180), (0, 90), (380, 320)],
    "success": [(1200, 80), (0, 40), (1800, 120)],
}


class Buzzer:
    def __init__(self):
        self.passive = config.BUZZER_PASSIVE
        self.volume = config.BUZZER_VOLUME
        self.muted = False
        self.sequence = []
        self.index = 0
        self.step_start = 0
        self.active = False

        if self.passive:
            self.pwm = machine.PWM(machine.Pin(config.BUZZER_PIN))
            self.pwm.duty_u16(0)
        else:
            self.pin = machine.Pin(config.BUZZER_PIN, machine.Pin.OUT, value=0)

    def silence(self):
        if self.passive:
            self.pwm.duty_u16(0)
        else:
            self.pin.value(0)

    def stop(self):
        self.sequence = []
        self.index = 0
        self.active = False
        self.silence()

    def apply_step(self, step):
        frequency, _ = step
        if frequency <= 0:
            self.silence()
            return
        if self.passive:
            self.pwm.freq(frequency)
            self.pwm.duty_u16(int(65535 * self.volume * 0.5))
        else:
            self.pin.value(1)

    def play(self, name):
        if self.muted:
            return
        sequence = CUES.get(name)
        if not sequence:
            return
        self.stop()
        self.sequence = sequence
        self.index = 0
        self.step_start = time.ticks_ms()
        self.active = True
        self.apply_step(sequence[0])

    def set_muted(self, muted):
        self.muted = bool(muted)
        if self.muted:
            self.stop()

    def toggle_muted(self):
        self.set_muted(not self.muted)
        return self.muted

    def tick(self, now):
        if not self.active:
            return
        _, duration = self.sequence[self.index]
        if time.ticks_diff(now, self.step_start) < duration:
            return
        self.index += 1
        if self.index >= len(self.sequence):
            self.stop()
            return
        self.step_start = now
        self.apply_step(self.sequence[self.index])
