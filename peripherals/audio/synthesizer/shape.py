# External libs
from scipy import interpolate as scipy_interpolate
import numpy as np

# Internal libs
from peripherals.audio.audio import Audio, Chunk

# General other
from math import ceil
from typing import List, Dict, Any, Callable


class Shape:
    """
    Applies a shape to audio objects
    """

    # Shape examples
    SHARP_START = {0.0: 0.0, 0.005: 1.0, 0.25: 0.5, 0.9: 0.1, 0.95: 0.0, 1.0: 0.0}
    ROUND_RIGHT_BIAS = {0.0: 0.0, 0.5: 0.75, 0.8: 0.4, 1.0: 0.1}
    FLAT_SHAPE = {0.0: 1.0, 1.0: 1.0}
    EXPONENTIAL_DECAY = {(x/20.0): pow(2.71, -x*x/5.0) for x in range(21)}

    # interpolator mode variables
    __scipy_interpolator: scipy_interpolate = None
    __min_interpolator_x: float = None
    __max_interpolator_x: float = None

    # function mode variables
    __fun: Callable = None
    __max_fun_mode_x: float = None

    def __init__(self,
                 y_or_xy_values_or_function: List[float] | Dict[float, float] | Callable[[Any], float],
                 kind: str,
                 length: float = None):

        if callable(y_or_xy_values_or_function):
            self.__fun = np.vectorize(y_or_xy_values_or_function)
            self.__max_fun_mode_x = length
        else:
            if isinstance(y_or_xy_values_or_function, list):
                keys = [i/len(y_or_xy_values_or_function) for i in range(len(y_or_xy_values_or_function))]
                vals = y_or_xy_values_or_function
            else:
                keys, vals = zip(*sorted(y_or_xy_values_or_function.items(), key=lambda x: x[0]))

            if length is not None:
                max_x = max(keys)
                keys = [key * length / max_x for key in keys]

            self.__scipy_interpolator = scipy_interpolate.interp1d(keys, vals, kind=kind)
            self.__min_interpolator_x = min(keys)
            self.__max_interpolator_x = max(keys)

    def apply(self, obj: Audio, stretch: bool = False) -> Audio:
        if not obj.chunks:
            return Audio([], sample_width=obj.sample_width, frame_rate=obj.frame_rate, channels=obj.channels)

        chunk_size: int = obj.chunks[0].frames()
        obj.normalise_chunks(chunk_size)

        total_frames: int = obj.frames()
        frame_rate: int = obj.frame_rate

        shape_chunks: List[Chunk] = []
        for i_chunk in range(ceil(total_frames / chunk_size)):
            # array of actual times:
            nparray: np.ndarray = (np.arange(chunk_size) + i_chunk * chunk_size) / frame_rate

            # stretching the shape is equivalent to compressing the space to shape-size
            factor: float = (self.__max_fun_mode_x or 1.0) / obj.seconds()
            if stretch:
                nparray *= factor

            # chunks outside the shape area are just zeros
            upper_cut_off: float = self.__max_fun_mode_x or self.__max_interpolator_x
            lower_cut_off: float = self.__min_interpolator_x
            if upper_cut_off and (nparray[0] > upper_cut_off or nparray[-1] < lower_cut_off):
                shape_chunks.append(Chunk.zeros(chunk_size, obj.sample_width, obj.using_float))
                continue

            # actual application
            min_index: int = np.searchsorted(nparray, lower_cut_off)
            max_index: int = np.searchsorted(nparray, upper_cut_off)

            front: np.ndarray
            mid: np.ndarray
            tail: np.ndarray
            front, mid, tail = np.split(nparray, [min_index, max_index])
            front.fill(0.0)
            tail.fill(0.0)
            if self.__fun:
                mid = self.__fun(mid)
            else:
                mid = self.__scipy_interpolator(mid)
            nparray = np.concatenate((front, mid, tail), None)
            shape_chunks.append(Chunk(nparray=nparray))

        shape_obj: Audio = Audio(shape_chunks,
                                 channels=obj.channels,
                                 frame_rate=frame_rate,
                                 sample_width=obj.sample_width)

        shape_obj *= obj

        return shape_obj
