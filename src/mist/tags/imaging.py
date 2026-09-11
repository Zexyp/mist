import logging
from enum import Enum, auto
from io import BytesIO
import mimetypes

import requests

from mist.log import announce_optional_module_error
from mist.metadata.scrape_utils import assert_status_code
from mist.utils import MistEnum

try:
    from PIL import Image
except ImportError as e:
    Image = None
    announce_optional_module_error(e)

logger = logging.getLogger(__name__)

class ImageAdjust(MistEnum):
    NONE = auto()
    ZOOM = auto()
    SCALED = auto()
    CROP = auto()
    STRETCH = auto()

def _get_format(name: str) -> tuple[str, str]:
    if name in ["jpg", "jpeg", "jfif"]:
        return ("JPEG", "image/jpeg")
    elif name == "png":
        return ("PNG", "image/png")
    else:
        raise ValueError(f"unknown image format '{name}'")

def _get_format_mime(mime: str):
    if mime == "image/jpeg":
        return ("JPEG", "image/jpeg")
    elif mime == "image/png":
        return ("PNG", "image/png")
    else:
        raise ValueError(f"unknown mime type '{mime}'")


def _resize(image: Image.Image, target_size: tuple[int, int], strategy: ImageAdjust) -> Image.Image:
    target_w, target_h = target_size
    w, h = image.size
    bg = (0, 0, 0)

    logger.debug(f"resizing to {target_w}x{target_h} using {strategy.name}")

    match strategy:
        case ImageAdjust.NONE:
            # fuck you!
            mode = image.mode
            pixels = list(image.getdata())
            match mode:
                case "RGB":
                    pad_color = (0, 0, 0)
                case "RGBA":
                    pad_color = (0, 0, 0, 255)
                case "L":
                    pad_color = 0
                case _:
                    assert False
            needed = target_w * target_h
            pixels = pixels[:needed]
            if len(pixels) < needed:
                pixels += [pad_color] * (needed - len(pixels))
            out = Image.new(mode, (target_w, target_h))
            out.putdata(pixels)
            return out
        case ImageAdjust.ZOOM:
            scale = max(target_w / w, target_h / h)
            new_size = (int(w * scale), int(h * scale))
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            x = (new_size[0] - target_w) // 2
            y = (new_size[1] - target_h) // 2
            return resized.crop((x, y, x + target_w, y + target_h))
        case ImageAdjust.SCALED:
            scale = min(target_w / w, target_h / h)
            new_size = (int(w * scale), int(h * scale))
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            canvas = Image.new(image.mode, target_size, bg)
            offset = ((target_w - new_size[0]) // 2, (target_h - new_size[1]) // 2)
            canvas.paste(resized, offset)
            return canvas
        case ImageAdjust.CROP:
            canvas = Image.new(image.mode, target_size, bg)
            offset = ((target_w - w) // 2, (target_h - h) // 2)
            canvas.paste(image, offset)
            return canvas
        case ImageAdjust.STRETCH:
            return image.resize(target_size, Image.Resampling.LANCZOS)

    raise ValueError(f"unknown image adjustment '{strategy}'")

def process(url: str, options: dict) -> tuple[str, BytesIO]:
    logger.debug(f"downloading {url}")
    response = requests.get(url)
    assert_status_code(response)

    default_mime = response.headers['content-type']
    if not Image:
        return (default_mime, response.content)

    logger.debug(f"retrieved mime {default_mime}")

    image = Image.open(BytesIO(response.content))
    if "size" in options:
        image = _resize(image, options["size"], ImageAdjust(options.get("adjustment", "none")))

    format, mime = _get_format(options["format"]) if "format" in options else _get_format_mime(default_mime)

    if "convert" in options:
        image = image.convert(options["convert"])

    params = {}
    if "subsampling" in options: params["subsampling"] = options["subsampling"]

    if "compression" in options:
        if format == "PNG":
            params["compress_level"] = options["compression"]
        if format == "JPEG":
            params["quality"] = options["compression"]

    assert format
    data = BytesIO()
    image.save(data, format=format, params=params)
    # hmmm, were we rly writing 0 bytes :sob:
    data.seek(0)
    return (mime, data)
