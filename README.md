# LaunchpadSequencer
A simple sequencer that uses a Novation Launchpad to send signals to a "Midi Through" device

# Setup
- Requires a Novation Launchpad (mini MK3 in my case) and `mido` for Python
- When run, it looks for something like `Launchpad MIDI 2` as the input device, and something like `Midi Through` as the output device (it would be easy to change the output device but `Midi Through` works for my purposes)
- It requires some MIDI compliant program to be listening on the `Midi Through` device to accept the notes. Notes come in on Channels 1-4 depending on the current sequencer grid (starting at C4)

# Usage
- When running, a sweep will move across the grid
- Clicking on any button on the main grid will toggle a note, which will play when the sweep hits it
- The lowest note in the column will be a C4, and the highest note by default is a C5
- Each grid sends a MIDI note on a separate channel, so I have setup separate instruments that listen to each channel

## Default keys
- The first two CC keys (Up and Down) change the BPM. The initial BPM is 60, which works because these are all quarter notes anyway
- The Left key turns on Silent mode for the current grid, which causes notes to not play
- The Right key turns on Note Eater Mode, which erases notes when they are played. Useful for a lead instrument so it doesn't sound as stale
- The next three CCs (Session, Drums, and Keys in my case) change the current Scale for the song (Major, Minor, and Pentatonic)
- The final top row CC (User in my case) resets the current grid
- Down the left right side, the top four control which grid is currently shown

