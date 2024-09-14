from typing import List, Any


class Note:
    """
    A generic english note
    """
    NOTES: List[str] = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
    ROOT12OF2: float = 1.059463
    A4PITCH: float = 440.0

    def __init__(self, note, octave=4):
        self.octave = octave
        if isinstance(note, int):
            self.index = note
            self.note = Note.NOTES[note]
        elif isinstance(note, str):
            self.note = note.strip().lower()
            self.index = Note.NOTES.index(self.note)

    def transpose(self, half_steps: int):
        octave_delta, note = divmod(self.index + half_steps, 12)
        return Note(note, self.octave + octave_delta)

    def frequency(self):
        return self.A4PITCH * pow(self.ROOT12OF2, self.half_steps_from(Note('A')))

    def __float__(self):
        return self.frequency()

    def half_steps_from(self, other: Any) -> int:
        return (self.octave - other.octave) * len(Note.NOTES) + self.index - other.index