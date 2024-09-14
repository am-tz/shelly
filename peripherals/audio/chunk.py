# External libs
import numpy as np

# General utilities
from typing import Tuple, Any


# TODO: what about channels - currently every audio involved has only one, but I think we have to adjust the frame
#       count and think about how SoundShapes will work with multiple channels.
class Chunk:
    """
    A section of an AudioObject that can represent itself as bytes or as a numpy array, and convert
    between different number formats

    It does not know about frame rate or channels
    """

    _bytes: bytes = None
    _d_type: np.dtype = None
    _nparray: np.ndarray = None
    _bytes_up_to_date: bool = None

    def __init__(self, raw_bytes: bytes = None,
                 sample_width: int = None,
                 using_float: bool = None,
                 nparray: np.ndarray = None):
        if raw_bytes is not None:
            assert sample_width and using_float is not None
            self._bytes = raw_bytes
            self._bytes_up_to_date = True
            self._d_type = np.dtype(f"{'f' if using_float else 'i'}{sample_width}")
        else:
            assert nparray is not None
            assert using_float is None and sample_width is None
            self._nparray = nparray
            self._d_type = nparray.dtype
            self._bytes_up_to_date = False

    def frames(self) -> int:
        if self._nparray is not None:
            return len(self._nparray)
        else:
            return len(self._bytes) // self._d_type.alignment

    def tobytes(self) -> bytes:
        if not self._bytes_up_to_date:
            self._bytes = self._nparray.tobytes()
            self._bytes_up_to_date = True
        return self._bytes

    def sample_width(self) -> int:
        return self._d_type.alignment

    def using_float(self) -> bool:
        return self._d_type.kind == 'f'

    def nparray(self) -> np.ndarray:
        if self._nparray is None:
            self._nparray = np.frombuffer(self._bytes, dtype=self._d_type)
        return self._nparray

    # TODO: Account for different audio formats to make energies comparable
    def mean_square_energy(self) -> float:
        return sum(x**2/self.frames() for x in self.nparray())

    def to_float(self, sample_width: int = 4) -> None:
        if self.using_float() and self.sample_width() == sample_width:
            return
        elif self.using_float():
            dt_to = np.dtype(f"f{sample_width}")
            self._nparray = self.nparray().astype(dt_to)
            self._d_type = dt_to
            self._bytes_up_to_date = False
        else:
            dt_to = np.dtype(f"f{sample_width}")
            i = np.iinfo(self._d_type)
            self._nparray = (self.nparray().astype(dt_to) / abs(i.min)).clip(-1.0, 1.0)
            self._d_type = dt_to
            self._bytes_up_to_date = False

    def to_int(self, sample_width: int = 2) -> None:
        if not self.using_float() and self.sample_width() == sample_width:
            return
        elif not self.using_float():
            self.to_float(8)
            self.to_int(sample_width)
        else:
            dt_to = np.dtype(f"i{sample_width}")
            i = np.iinfo(dt_to)
            self._nparray = (self.nparray() * abs(i.min)).clip(i.min, i.max).astype(dt_to)
            self._d_type = dt_to
            self._bytes_up_to_date = False

    def to_d_type(self, d_type: np.dtype) -> None:
        if d_type.kind == "f":
            self.to_float(d_type.alignment)
        else:
            assert d_type.kind == "i"
            self.to_int(d_type.alignment)

    def split(self, after_frame) -> Tuple[Any, Any]:
        front, tail = np.split(self.nparray(), [after_frame])
        return Chunk(nparray=front), Chunk(nparray=tail)

    def append(self, other: Any) -> None:
        assert isinstance(other, Chunk)
        self._nparray = np.concatenate((self.nparray(), other.nparray()))
        self._bytes_up_to_date = False

    def fill_with_zeros(self, target_size) -> None:
        missing_fields: int = target_size - self.frames()
        if missing_fields > 0:
            self.append(Chunk(nparray=np.zeros(missing_fields, dtype=self._d_type)))

    @staticmethod
    def zeros(target_size: int, sample_width: int, using_float: bool) -> Any:
        chunk = Chunk(b'', sample_width, using_float)
        chunk.fill_with_zeros(target_size)
        return chunk

    def __add__(self, other: Any):
        result = Chunk(nparray=self.nparray())
        if isinstance(other, Chunk):
            result.to_d_type(other._d_type)
            result._nparray = result.nparray() + other.nparray()
        elif isinstance(other, np.ndarray):
            result.to_d_type(other.dtype)
            result._nparray = result.nparray() + other
        else:
            assert isinstance(other, int) or isinstance(other, float)
            result._nparray = result.nparray() + other

        result._bytes_up_to_date = False
        return result

    def __mul__(self, other: Any):
        result = Chunk(nparray=self.nparray())
        if isinstance(other, Chunk):
            result.to_d_type(other._d_type)
            result._nparray = result.nparray() * other.nparray()
        elif isinstance(other, np.ndarray):
            result.to_d_type(other.dtype)
            result._nparray = result.nparray() * other
        else:
            assert isinstance(other, int) or isinstance(other, float)
            result._nparray = result.nparray() * other

        result._bytes_up_to_date = False
        return result

    def __truediv__(self, other: Any):
        result = Chunk(nparray=self.nparray())
        if isinstance(other, Chunk):
            result.to_d_type(other._d_type)
            result._nparray = result.nparray() / other.nparray()
        elif isinstance(other, np.ndarray):
            result.to_d_type(other.dtype)
            result._nparray = result.nparray() / other
        else:
            assert isinstance(other, int) or isinstance(other, float)
            result._nparray = result.nparray() / other

        result._bytes_up_to_date = False
        return result
