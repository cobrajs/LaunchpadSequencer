from LaunchpadControl import LaunchpadControl
from mido import Message

SCALES = [
    [60, 62, 64, 65, 67, 69, 71, 72],  # Major
    [60, 62, 63, 65, 67, 69, 70, 72],  # Minor
    [60, 62, 64, 67, 69, 72, 74, 76],  # Pentatonic
]

class Grid:
    def __init__(self, control, on_color=3):
        self.grid = [[False for x in range(8)] for y in range(8)]
        self.control = control

        self.on_color = on_color

        self.silent_mode = False
        self.note_eater_mode = False

    def set(self, xy, value, note=None):
        self.grid[xy[1]][xy[0]] = value
        if not note:
            note = LaunchpadControl.xy_to_note(xy)
        if value:
            self.control.note_on(note, self.on_color)
        else:
            self.control.note_off(note)

    def get(self, xy):
        return self.grid[xy[1]][xy[0]]

    def toggle_note(self, xy, note):
        if self.get(xy):
            self.set(xy, False, note)
        else:
            self.set(xy, True, note)

    def reset(self):
        for y, row in enumerate(self.grid):
            for x, column in enumerate(row):
                self.set((x, y), False)

    def clear(self):
        for y, row in enumerate(self.grid):
            for x, column in enumerate(row):
                self.control.note_off(LaunchpadControl.xy_to_note((x, y)))

    def render(self):
        for y, row in enumerate(self.grid):
            for x, column in enumerate(row):
                if column:
                    self.control.note_on(LaunchpadControl.xy_to_note((x, y)), self.on_color)

    def column_off(self, column):
        for y in range(8):
            xy = (column, y)
            if self.get(xy):
                continue
            self.control.note_off(LaunchpadControl.xy_to_note(xy))

    def column_on(self, column):
        for y in range(8):
            xy = (column, y)
            if self.get(xy):
                continue
            self.control.note_dim(LaunchpadControl.xy_to_note(xy))

    def toggle_silent_mode(self):
        self.silent_mode = not self.silent_mode
        return self.silent_mode

    def toggle_note_eater(self):
        self.note_eater_mode = not self.note_eater_mode
        return self.note_eater_mode

    def get_column_on(self, column):
        if self.silent_mode:
            return []
        notes = [y for y in range(8) if self.get((column, y))]
        if self.note_eater_mode:
            for y in range(8):
                self.set((column, y), False)
        return notes


class Sequencer:
    def __init__(self, control, output, transport=None):
        self.grids = []
        self.current_grid = 0
        self.current_column = 0
        self.transport = transport
        self.output = output

        self.current_scale = SCALES[0]

    def y_to_note(self, y):
        return self.current_scale[y]

    def change_scale(self, scale_index):
        self.current_scale = SCALES[scale_index]

    def add_grid(self, grid):
        self.grids.append(grid)

    def get_current_grid(self):
        if len(self.grids) > 0:
            return self.grids[self.current_grid]
        return None

    def set_current_grid(self, grid_index):
        self.grids[self.current_grid].clear()
        self.current_grid = grid_index
        self.grids[self.current_grid].render()

    def toggle_silent_mode(self):
        current_grid = self.get_current_grid()
        if current_grid:
            return current_grid.toggle_silent_mode()
        return False

    def toggle_note_eater(self):
        current_grid = self.get_current_grid()
        if current_grid:
            return current_grid.toggle_note_eater()
        return False

    def step(self):
        note_length = max(self.transport.time_step * 0.9, 0.25)
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.column_off(self.current_column)
        self.current_column += 1
        if self.current_column >= 8:
            self.current_column = 0
        for grid_index, grid in enumerate(self.grids):
            notes = [self.y_to_note(y) for y in grid.get_column_on(self.current_column)]
            if notes:
                self.output.send_notes(notes, note_length, grid_index)
        if current_grid:
            current_grid.column_on(self.current_column)

    def toggle_note(self, xy, note):
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.toggle_note(xy, note)

    def clear(self):
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.clear()

    def reset_grid(self):
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.reset()

