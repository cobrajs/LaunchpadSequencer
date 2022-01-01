from mido import Message
from time import time

class Transport:
    def __init__(self, bpm):
        self.bpm = bpm
        self.time_step = 0
        self.clock_step = 0

        self.last_time = time()

        self.current_time_step = 0
        self.current_clock_step = 0

        self.time_step_callback = None
        self.launchpad_control = None

        self.set_bpm(bpm)

    def set_bpm(self, bpm):
        self.bpm = bpm
        self.time_step = 60 / self.bpm / 4
        self.clock_step = self.time_step / 12
        print("New BPM: ", self.bpm)

    def increase_bpm(self, amount):
        self.set_bpm(min(self.bpm  + amount, 200))

    def decrease_bpm(self, amount):
        self.set_bpm(max(self.bpm - amount, 20))

    def update_time(self):
        delta = time() - self.last_time

        self.current_time_step += delta
        if self.current_time_step >= self.time_step:
            self.current_time_step = 0
            if self.time_step_callback:
                self.time_step_callback()

        self.current_clock_step += delta
        if self.current_clock_step >= self.clock_step:
            if self.launchpad_control:
                self.launchpad_control.send_message(Message('clock'))
            self.current_clock_step = 0

        self.last_time = time()


