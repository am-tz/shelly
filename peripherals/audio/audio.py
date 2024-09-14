# External libs
import wave
from numpy import ndarray
from soundfile import SoundFile

# Internal libs
from peripherals.audio.chunk import Chunk

from infra.log.loggable import Loggable

# General other
from io import BytesIO
from copy import deepcopy
from typing import Tuple, List, Any


class Audio(Loggable):
    """
    A generic representation of and audio object that supports cutting and format conversions - to some extent.
    """

    sample_width: int = None
    channels: int = None
    frame_rate: int = None
    using_float: bool = None

    chunks: List[Chunk] = None

    DEFAULT_CHUNK_SIZE = 1024
    DEFAULT_FRAME_RATE = 44100
    DEFAULT_CHANNELS = 1

    @staticmethod
    def _using_float_convention(sample_width: int):
        return sample_width > 2

    def normalise_chunks(self, chunk_size: int) -> None:
        new_chunks: List[Chunk] = []
        target_frames = chunk_size
        for chunk in self.chunks:
            remaining = chunk
            while remaining.frames() > 0:
                new_chunk, remaining = remaining.split(target_frames)
                if target_frames < chunk_size:
                    new_chunks[-1].append(new_chunk)
                    target_frames = chunk_size - new_chunks[-1].frames()
                    if target_frames == 0:
                        target_frames = chunk_size
                else:
                    new_chunks.append(new_chunk)

        self.chunks = new_chunks

    def extend_zeros(self, chunk_size: int, target_number_of_chunks: int):
        self.chunks[-1].fill_with_zeros(chunk_size)
        missing_chunks = target_number_of_chunks - len(self.chunks)
        for i in range(max(missing_chunks, 0)):
            self.chunks.append(Chunk.zeros(chunk_size, self.sample_width, self.using_float))

    def __init_from_wav_filename(self, filename: str, chunk_size: int) -> None:
        with wave.open(filename, "rb") as wf:
            self.channels = wf.getnchannels()
            self.frame_rate = wf.getframerate()
            self.sample_width = wf.getsampwidth()
            self.using_float = self._using_float_convention(self.sample_width)
            self.chunks = []
            while len(data := wf.readframes(chunk_size or self.DEFAULT_CHUNK_SIZE)):
                chunk = Chunk(raw_bytes=data,
                              sample_width=self.sample_width,
                              using_float=self.using_float)
                self.chunks.append(chunk)

    def __init_from_wav_buffer(self, buffer: BytesIO, chunk_size: int) -> None:
        with wave.open(buffer, "rb") as wf:
            self.channels = wf.getnchannels()
            self.frame_rate = wf.getframerate()
            self.sample_width = wf.getsampwidth()
            self.using_float = self._using_float_convention(self.sample_width)
            self.chunks = []
            while len(data := wf.readframes(chunk_size or self.DEFAULT_CHUNK_SIZE)):
                chunk = Chunk(raw_bytes=data,
                              sample_width=self.sample_width,
                              using_float=self.using_float)
                self.chunks.append(chunk)

    def __init_from_chunks(self, chunks: List[Chunk],
                           channels: int,
                           frame_rate: int,
                           sample_width: int,
                           max_chunk_size: int) -> None:
        assert chunks
        self.chunks = chunks
        assert channels
        self.channels = channels
        assert frame_rate
        self.frame_rate = frame_rate
        assert sample_width
        self.sample_width = sample_width
        self.using_float = self._using_float_convention(sample_width)

        if max_chunk_size is not None:
            self.normalise_chunks(max_chunk_size)

    def __init_from_ogg_buffer(self, buffer: BytesIO, chunk_size: int):
        with SoundFile(buffer, 'r') as sound_file:
            self.channels = sound_file.channels
            self.frame_rate = sound_file.samplerate
            self.sample_width = 2
            self.using_float = False
            self.chunks = []
            data = sound_file.read(chunk_size or self.DEFAULT_CHUNK_SIZE, dtype='int16')
            while len(data) > 0:
                chunk = Chunk(raw_bytes=data.tobytes(),
                              sample_width=2,
                              using_float=False)
                self.chunks.append(chunk)
                data = sound_file.read(chunk_size or self.DEFAULT_CHUNK_SIZE, dtype='int16')

    def __init__(self, chunks: List[Chunk] | List[ndarray] | Chunk | ndarray = None, byte_chunks: List[bytes] = None,
                 channels: int = None, frame_rate: int = None, sample_width: int = None, ogg_buffer: BytesIO = None,
                 wav_buffer: BytesIO = None, chunk_size: int = None, wav_filename: str = None):

        super().__init__()
        
        if wav_filename is not None:
            assert not (chunks or byte_chunks or channels or frame_rate or sample_width)
            assert ogg_buffer is None
            assert wav_buffer is None
            self.__init_from_wav_filename(wav_filename, chunk_size)
        elif wav_buffer is not None:
            assert not (chunks or byte_chunks or channels or frame_rate or sample_width)
            assert ogg_buffer is None
            self.__init_from_wav_buffer(wav_buffer, chunk_size)
        elif ogg_buffer is not None:
            assert (not (chunks or byte_chunks or channels or frame_rate or sample_width))
            self.__init_from_ogg_buffer(ogg_buffer, chunk_size)
        elif byte_chunks is not None:
            assert chunks is None
            using_float = self._using_float_convention(sample_width)
            parsed_chunks = [Chunk(byte_chunk, sample_width, using_float) for byte_chunk in byte_chunks]
            self.__init_from_chunks(parsed_chunks, channels, frame_rate, sample_width, chunk_size)
        else:
            if not isinstance(chunks, list):
                chunks = [chunks]
            if chunks and isinstance(chunks[0], ndarray):
                chunks = [Chunk(nparray=chunk) for chunk in chunks]
            self.__init_from_chunks(chunks,
                                    channels or self.DEFAULT_CHANNELS,
                                    frame_rate or self.DEFAULT_FRAME_RATE,
                                    sample_width or chunks[0].sample_width(),
                                    chunk_size)

    def __write(self, target: BytesIO | str) -> None:
        with wave.open(target, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.frame_rate)
            wf.writeframes(b''.join([chunk.tobytes() for chunk in self.chunks]))

    def pop(self, index: int = 0):
        if not self.chunks:
            return None
        chunk: Chunk = self.chunks.pop(index)
        return Audio(chunks=chunk,
                     channels=self.channels,
                     frame_rate=self.frame_rate,
                     sample_width=self.sample_width,
                     chunk_size=chunk.frames())

    def stream(self) -> BytesIO:
        buffer = BytesIO()
        self.__write(buffer)
        buffer.seek(0)
        return buffer

    def save(self, filename: str) -> None:
        self.__write(filename)

    def seconds(self):
        return sum(chunk.frames() for chunk in self.chunks) / self.frame_rate

    def frames(self):
        return sum(chunk.frames() for chunk in self.chunks)

    def root_mean_square_energy(self) -> float:
        return sum(chk.mean_square_energy() * chk.frames() / self.frames() for chk in self.chunks) ** 0.5

    def __find_chunk_at(self, time: float, default_to_end: bool = False, loop: bool = False) -> int:
        if time is None:
            return len(self.chunks) if default_to_end else 0

        whole, frac = divmod(time, self.seconds())
        res = int(whole) * len(self.chunks)

        frames: int = 0
        target_frames: float = time * self.frame_rate
        for i, chunk in enumerate(self.chunks):
            frames += chunk.frames()
            if frames > target_frames:
                res += i
                break

        assert loop or 0 <= res <= len(self.chunks)
        return res

    def copy(self, start_time: float = None, end_time: float = None, loop: bool = True) -> Any:
        start_chunk = self.__find_chunk_at(start_time, False, loop)
        end_chunk = self.__find_chunk_at(end_time, True, loop)
        self._logger.debug(f"Copy start chunk: '{start_chunk}'")
        self._logger.debug(f"Copy end chunk: '{end_chunk}'")

        start_whole, start_mod_chunks = divmod(start_chunk, len(self.chunks))
        end_whole, end_mod_chunks = divmod(end_chunk, len(self.chunks))

        if loop and not start_whole == end_whole:
            whole_sections = max(end_whole - start_whole - 1, 0)
            chunks = self.chunks[start_mod_chunks:] + whole_sections * self.chunks + self.chunks[:end_mod_chunks]
        else:
            chunks = self.chunks[start_chunk:end_chunk]

        return Audio(chunks=chunks,
                     channels=self.channels,
                     frame_rate=self.frame_rate,
                     sample_width=self.sample_width)

    def cut_out(self, start_time: float = None, end_time: float = None) -> Any:
        start_chunk = self.__find_chunk_at(start_time, False)
        end_chunk = self.__find_chunk_at(end_time, True)
        self._logger.debug(f"Cut-out start chunk: '{start_chunk}'")
        self._logger.debug(f"Cut-out end chunk: '{end_chunk}'")
        res = Audio(chunks=self.chunks[start_chunk:end_chunk],
                    channels=self.channels,
                    frame_rate=self.frame_rate,
                    sample_width=self.sample_width)
        self.chunks = self.chunks[:start_chunk] + self.chunks[end_chunk:]
        return res

    def insert(self, other: Any, insertion_time: int = None) -> None:
        assert isinstance(other, Audio)
        assert other.frame_rate == self.frame_rate
        assert other.sample_width == self.sample_width
        assert other.using_float == self.using_float
        insertion_chunk = self.__find_chunk_at(insertion_time, True)
        self._logger.debug(f"Insertion before chunk: '{insertion_chunk}'")
        self.chunks = self.chunks[:insertion_chunk] + other.chunks + self.chunks[insertion_chunk:]

    def repeat(self, scalar: float | int) -> Any:
        assert isinstance(scalar, float) or isinstance(scalar, int)
        assert scalar >= 0
        return self.copy(end_time=self.seconds() * scalar, loop=True)

    def __to_int(self, sample_width: int = 2) -> None:
        if not self.using_float and self.sample_width == sample_width:
            return

        for chunk in self.chunks:
            chunk.to_int(sample_width)

        self.sample_width = sample_width
        self.using_float = False

    def __to_float(self, sample_width: int = 4) -> None:
        if self.using_float and self.sample_width == sample_width:
            return

        for chunk in self.chunks:
            chunk.to_float(sample_width)

        self.sample_width = sample_width
        self.using_float = True

    def to_format(self, sample_width: int, using_float: bool):
        if using_float:
            self.__to_float(sample_width)
        else:
            self.__to_int(sample_width)

    def to_standard_width(self) -> None:
        if self.using_float:
            self.__to_float()
        else:
            self.__to_int()

    def __align(self, other: Any) -> Tuple[Any, Any]:
        assert isinstance(other, Audio)
        assert self.channels == other.channels
        assert self.frame_rate == other.frame_rate
        self.normalise_chunks(self.DEFAULT_CHUNK_SIZE)
        other.normalise_chunks(self.DEFAULT_CHUNK_SIZE)
        working_length = max(len(self.chunks), len(other.chunks))
        if len(self.chunks) < len(other.chunks):
            shorter, longer = self, other
        else:
            longer, shorter = other, self
        res: Audio = deepcopy(shorter)
        res.to_format(longer.sample_width, longer.using_float)
        res.extend_zeros(self.DEFAULT_CHUNK_SIZE, working_length)
        longer.extend_zeros(self.DEFAULT_CHUNK_SIZE, working_length)
        return res, longer

    def __add__(self, other: Any):
        res, to_add = self.__align(other)
        for i in range(len(res.chunks)):
            res.chunks[i] += to_add.chunks[i]
        return res

    def __mul__(self, other: Any):
        if isinstance(other, Audio):
            res, to_mul = self.__align(other)
            for i in range(len(res.chunks)):
                res.chunks[i] *= to_mul.chunks[i]
        else:
            assert isinstance(other, float) or isinstance(other, int)
            res = deepcopy(self)
            for i in range(len(res.chunks)):
                res.chunks[i] *= other
        return res

    def __truediv__(self, other: Any):
        if isinstance(other, Audio):
            res, to_mul = self.__align(other)
            for i in range(len(res.chunks)):
                res.chunks[i] /= to_mul.chunks[i]
        else:
            assert isinstance(other, float) or isinstance(other, int)
            res = deepcopy(self)
            for i in range(len(res.chunks)):
                res.chunks[i] /= other
        return res


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    from os.path import dirname, pardir, join, realpath

    LoggingSetup()

    uncut_bam_path: str = realpath(join(dirname(realpath(__file__)), pardir, pardir, "files", "tests", "uncut_bam.wav"))
    uncut_bam: Audio = Audio(wav_filename=uncut_bam_path)

    bam: Audio = uncut_bam.copy(1.0, 1.11).repeat(4)
    bam.insert(uncut_bam.copy(1.0, 2.0))

    from peripherals.audio.output import Output
    from time import sleep

    print("Playing")
    with Output() as output:
        output.play(bam.copy())
        sleep(bam.seconds())
        print(bam.root_mean_square_energy())
