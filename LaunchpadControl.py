from mido import Message
import time

class KeyColor:
    ''' '''
    def __init__(self, on_color, off_color=None, channel=0):
        self.on_color = on_color
        self.off_color = off_color
        self.channel = channel

    def get_on_message(self, note):
        return Message('note_on', note=note, velocity=self.on_color, channel=self.channel)

    def get_off_message(self, note):
        if self.off_color:
            return Message('note_on', velocity=self.off_color, note=note)
        return Message('note_off', note=note)


class KeyGroup:
    ''' For setting up a group of keys to act as radio buttons '''
    def __init__(self, keys, key_color, default=None):
        self.keys = keys
        self.key_color = key_color
        self.active_key = default or keys[0]
        self.active = False

    def activate(self, message_sender):
        self.active = True
        self.toggle_key(message_sender, self.active_key)

    def toggle_key(self, message_sender, note=None):
        off_message = self.key_color.get_off_message(note)
        for off_key in self.keys:
            message_sender(off_message.copy(note=off_key))
        message_sender(self.key_color.get_on_message(note))

    def cleanup(self, message_sender):
        for button in self.keys:
            message_sender(Message('note_off', note=button))


class LaunchpadControl:
    def __init__(self, output, input):
        self.output = output
        self.input = input

        self.groups = {
            "Scales": KeyGroup((95, 96, 97), KeyColor(67, 1)),
            "Sequences": KeyGroup((89, 79, 69, 59), KeyColor(13, 11, 2)),
        }

        self.buttons = {
            "Up": 91,
            "Down": 92,
            "Left": 93,
            "Right": 94,
            "Reset": 98,
            "Pause": 19,
        }

        self.actions = {}
        self.group_actions = {}
        self.toggles = {}

    def set_programmer_mode(self):
        print("Setting Programmer Mode")
        sysex_header = (0, 32, 41, 2, 13)
        # SysEx message to set Programmer mode
        programmer_sysex = Message('sysex', data=sysex_header + (0, 127))
        self.output.send(programmer_sysex)

    def add_action(self, key, callback, arguments=None):
        key = self.buttons[key]
        self.actions[key] = (callback, arguments)

    def add_group_action(self, key, index, callback, arguments=None):
        group = self.groups[key]
        capture_key = group.keys[index]
        self.group_actions[capture_key] = (group, callback, arguments)
        if not group.active:
            group.activate(self.send_message)

    def add_toggle_action(self, key, key_color, callback, arguments=None):
        key = self.buttons[key]
        self.toggles[key] = (key_color, callback, arguments)
        self.send_message(key_color.get_off_message(key))

    def do_actions(self, message):
        for key, value in self.actions.items():
            if key == message.control:
                print("Doing action", value)
                self.do_callback(*value)
        for key, value in self.group_actions.items():
            if key == message.control:
                print("Doing group action", value)
                value[0].toggle_key(self.send_message, key)
                self.do_callback(*value[1:])
        for key, value in self.toggles.items():
            if key == message.control:
                print("Doing toggle", value)
                toggle_value = self.do_callback(*value[1:])
                if toggle_value:
                    self.send_message(value[0].get_on_message(key))
                else:
                    self.send_message(value[0].get_off_message(key))

    def do_callback(self, callback, argument):
        if argument != None:
            return callback(argument)
        return callback()

    def send_message(self, message):
        if not self.output.closed:
            self.output.send(message)
            time.sleep(0.001)

    def cleanup(self):
        # Turn off flashing logo
        self.send_message(Message('note_off', note=99))
        # Turn off groups
        for group in self.groups.values():
            group.cleanup(self.send_message)
        # Turn off buttons
        for button in self.buttons.values():
            self.send_message(Message('note_off', note=button))

    def note_on(self, note, color):
        self.send_message(Message('note_on', note=note, velocity=color))

    def note_off(self, note):
        self.send_message(Message('note_off', note=note))

    def note_dim(self, note):
        self.send_message(Message('note_on', velocity=1, note=note))

    @staticmethod
    def note_to_xy(note):
        return (note % 10 - 1, note // 10 - 1)

    @staticmethod
    def xy_to_note(xy):
        return (xy[0] + 1) + (xy[1] + 1) * 10

