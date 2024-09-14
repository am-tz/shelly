from peripherals.audio.synthesizer.note import Note
from bisect import bisect_left
from typing import List


class Scale:
    """
    A class to represent an arbitrary half-step based scale.
    The scale is represented by a list of consecutive half-steps from a root note.
    """

    A_ROOT: Note = Note("A", 3)
    C_ROOT: Note = Note("C", 4)
    MAJOR: List[int] = [2, 2, 1, 2, 2, 2, 1]
    NATURAL_MINOR: List[int] = [2, 1, 2, 2, 1, 2, 2]
    HARMONIC_MINOR: List[int] = [2, 1, 2, 2, 1, 3, 1]
    MELODIC_MINOR: List[int] = [2, 1, 2, 2, 2, 2, 1]
    ALL_HALF_TONES: List[int] = [1]

    def __init__(self, root: Note, intervals: List[int]):
        self.root = root
        self.intervals = intervals
        self.half_steps_per_scale = sum(intervals)
        self.accumulated_half_steps = [sum(intervals[:(i + 1)]) for i in range(len(intervals))]

    def get(self, index: int) -> Note:
        full_scales_distance: int = index // len(self.intervals)
        additional_scale_steps: int = index % len(self.intervals)
        half_steps_from_root: int = full_scales_distance * self.half_steps_per_scale
        if additional_scale_steps > 0:
            half_steps_from_root += self.accumulated_half_steps[additional_scale_steps - 1]

        return self.root.transpose(half_steps_from_root)

    def index(self, note: Note) -> int:
        half_steps_from_root: int = note.half_steps_from(self.root)
        full_scales_distance: int = half_steps_from_root // self.half_steps_per_scale
        additional_half_steps: int = half_steps_from_root % self.half_steps_per_scale
        if additional_half_steps == 0:
            return full_scales_distance * len(self.intervals)

        scale_steps_from_shifted_root = bisect_left(self.accumulated_half_steps, additional_half_steps)
        assert (scale_steps_from_shifted_root < len(self.intervals))
        assert (self.accumulated_half_steps[scale_steps_from_shifted_root] == additional_half_steps)

        return full_scales_distance * len(self.intervals) + scale_steps_from_shifted_root

    def transpose(self, note, interval) -> Note:
        return self.get(self.index(note) + interval)
