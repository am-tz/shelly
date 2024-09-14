# Internal libs
from peripherals.audio.synthesizer.scale import Scale, Note
from peripherals.audio.audio import Audio
from peripherals.audio.synthesizer.shape import Shape

# General utilities
import numpy as np
from typing import List, Dict


class Synthesizer:

    # Bit rate
    DEFAULT_RATE = 44100

    # Harmonics
    CLEAN_HARMONICS = [2.0, 4.0, 8.0]
    ALL_HARMONICS = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    NO_HARMONICS = []

    # Chords
    TWO_THIRDS = [2, 4]
    FULL_THIRDS = [2, 4, 6, 8]

    def __init__(self, rate=DEFAULT_RATE, default_length=1.0):
        self.rate = rate
        self.default_length = default_length

    def sine(self, frequency, length=None) -> Audio:
        signal_size = int((self.default_length if length is None else length) * self.rate)
        factor = float(frequency) * (np.pi * 2) / self.rate
        return Audio(np.sin(np.arange(signal_size) * factor))

    # Gives bytes for the requested frequency plus harmonic overtones
    def harmonics(self, freq: float, harmonics: List[float], weights: List[float],  length: int = None) -> Audio:

        if weights is None:
            weights = [1/(h*h) for h in harmonics]

        assert(len(harmonics) == len(weights))

        wave: Audio = self.sine(freq, length)
        for harmonic, weight in zip(harmonics, weights):
            wave += self.sine(freq * harmonic, length) * weight

        return wave / (sum(weights) + 1.0)

    # Gives bytes for the requested frequency with overtones and volume shape
    def pluck(self, note: Note,
              tone_shape: Dict[float, float],
              harmonics: List[float],
              weights: List[float] = None,
              length=None) -> Audio:

        pluck_obj: Audio = self.harmonics(note.frequency(), harmonics, weights, length)
        return Shape(tone_shape, 'slinear').apply(pluck_obj)

    def generic_chord(self,
                      n: int,
                      chord_scale: Scale,
                      scale_steps: List[int],
                      tone_shape: Dict[float, float],
                      harmonics: List[float],
                      weights: List[float] = None,
                      length=None) -> Audio:

        chord_root: Note = chord_scale.get(n)
        chord_chunk: Audio = self.pluck(chord_root, tone_shape, harmonics, weights, length)
        for steps in scale_steps:
            chord_chunk += self.pluck(chord_scale.transpose(chord_root, steps), tone_shape, harmonics, weights, length)

        return chord_chunk * 0.3

    def chord(self,
              note: Note,
              is_major: bool = True,
              tone_shape: Dict[float, float] = None,
              harmonics: List[float] = None,
              weights: List[float] = None,
              length=None) -> Audio:

        if tone_shape is None:
            tone_shape = Shape.SHARP_START
        if harmonics is None:
            harmonics = self.CLEAN_HARMONICS

        scale: Scale = Scale(note, Scale.MAJOR if is_major else Scale.HARMONIC_MINOR)

        return self.generic_chord(0, scale, self.TWO_THIRDS, tone_shape, harmonics, weights, length)


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from peripherals.audio.output import Output
    from peripherals.audio.audio import Audio

    sb = Synthesizer(default_length=0.5)
    c_major = Scale(Note("C", 4), Scale.MAJOR)

    def example_chord(key: int, length: float) -> Audio:
        return sb.chord(c_major.get(key),
                        tone_shape=Shape.EXPONENTIAL_DECAY,
                        harmonics=sb.NO_HARMONICS,
                        length=length)

    chords: List[Audio] = [example_chord(i, 0.5) for i in range(4)]
    chords += [example_chord(4, 1.0)] * 2
    chords += [example_chord(5, 0.5)] * 4
    chords += [example_chord(4, 2.0)]
    chords += [example_chord(3, 0.5)] * 4
    chords += [example_chord(2, 1.0)] * 2
    chords += [example_chord(4, 0.5)] * 4
    chords += [example_chord(0, 2.0)]

    output: Output = Output()
    for audio in chords:
        output.play(audio)
    output.close()
