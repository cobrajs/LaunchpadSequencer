#!/usr/bin/python

from mido import Message
import mido, sys, time, threading

from Transport import Transport
from LaunchpadControl import LaunchpadControl, KeyColor
from Sequencer import Sequencer, Grid

all_output_names = mido.get_output_names()
output_ports = [output for output in all_output_names if 'Launchpad' in output]
input_ports = [input for input in all_output_names if 'Launchpad' in input]

if len(output_ports) < 2 or len(input_ports) < 2:
    sys.exit('Missing Launchpad MIDI device')

daw_out_name = [output for output in output_ports if 'MIDI 1' in output].pop(0)
midi_out_name = [output for output in output_ports if 'MIDI 2' in output].pop(0)
midi_in_name = [input for input in input_ports if 'MIDI 2' in input].pop(0)
through_out_name = [output for output in all_output_names if 'Midi Through' in output].pop(0)

if not daw_out_name or not midi_out_name or not midi_in_name:
    sys.exit('Missing Launchpad MIDI ports')

#daw_out = mido.open_output(daw_out_name)
midi_out = mido.open_output(midi_out_name)
midi_in = mido.open_input(midi_in_name)
through_out = mido.open_output(through_out_name)

launchpad_control = LaunchpadControl(midi_out, midi_in)

class ThroughControl:
    def __init__(self, output):
        self.output = output

    def play(self, note, length):
        pass

    def send_notes(self, notes, length, channel):
        for note in notes:
            x = threading.Thread(target=self.short_note, args=(note, length, channel,))
            x.start()

    def short_note(self, note, length, channel=0):
        self.output.send(Message('note_on', note=note, velocity=60, channel=channel))
        time.sleep(length)
        self.output.send(Message('note_off', note=note, channel=channel))

through_control = ThroughControl(through_out)

sequencer = Sequencer(launchpad_control, through_control)

transport = Transport(60)
transport.time_step_callback = sequencer.step
transport.launchpad_control = launchpad_control

sequencer.transport = transport

try:
    launchpad_control.set_programmer_mode()

    launchpad_control.send_message(Message('note_on', channel=1, note=99, velocity=21))

    launchpad_control.add_action("Up", transport.increase_bpm, 10)
    launchpad_control.add_action("Down", transport.decrease_bpm, 10)
    launchpad_control.add_action("Reset", sequencer.reset_grid)

    launchpad_control.add_toggle_action("Left", KeyColor(57, 59, 1), sequencer.toggle_silent_mode)
    launchpad_control.add_toggle_action("Right", KeyColor(60, 11, 1), sequencer.toggle_note_eater)

    launchpad_control.add_group_action("Scales", 0, sequencer.change_scale, 0)
    launchpad_control.add_group_action("Scales", 1, sequencer.change_scale, 1)
    launchpad_control.add_group_action("Scales", 2, sequencer.change_scale, 2)

    launchpad_control.add_group_action("Sequences", 0, sequencer.set_current_grid, 0)
    launchpad_control.add_group_action("Sequences", 1, sequencer.set_current_grid, 1)
    launchpad_control.add_group_action("Sequences", 2, sequencer.set_current_grid, 2)
    launchpad_control.add_group_action("Sequences", 3, sequencer.set_current_grid, 3)

    sequencer.add_grid(Grid(launchpad_control, 3))
    sequencer.add_grid(Grid(launchpad_control, 17))
    sequencer.add_grid(Grid(launchpad_control, 114))
    sequencer.add_grid(Grid(launchpad_control, 37))

    sequencer.clear()
    print("added all controls")

    while True:
        transport.update_time()

        for msg in midi_in.iter_pending():
            print(msg)
            if msg.type == 'note_on' and msg.velocity > 0:
                xy = LaunchpadControl.note_to_xy(msg.note)
                sequencer.toggle_note(xy, msg.note)
            elif msg.is_cc() and msg.value > 0:
                launchpad_control.do_actions(msg)

finally:
    print("Cleaning up interface")
    sequencer.clear()
    launchpad_control.send_message(Message('note_off', note=99))
    launchpad_control.cleanup()
    #daw_out.close()
    midi_out.reset()
    midi_out.close()
    midi_in.close()
