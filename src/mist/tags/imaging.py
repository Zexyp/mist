from enum import Enum, auto

from mist.utils import MistEnum


class ImageAdjust(MistEnum):
    NONE = auto()
    ZOOM = auto()
    PAD = auto()
    CROP = auto()
    STRETCH = auto()
