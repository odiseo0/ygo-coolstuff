from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageFilter
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style


RGBColor = tuple[int, int, int]


@dataclass(frozen=True)
class RenderOptions:
    background: RGBColor = (0, 0, 0)
    sharpen: bool = True

    def to_cache_key(self) -> tuple:
        return (self.background, self.sharpen)


class HalfBlockImage:
    def __init__(self, image: Image.Image, viewport_width: int, viewport_height: int) -> None:
        self.image = image
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        image = self.image
        image_width, image_height = image.size
        image_rows = (image_height + 1) // 2

        top_padding = max((self.viewport_height - image_rows) // 2, 0)
        left_padding = max((self.viewport_width - image_width) // 2, 0)

        background = Style.null()
        newline = Segment("\n", background)

        pixels = image.load()
        color_cache: dict[RGBColor, Color] = {}

        for _ in range(top_padding):
            yield Segment(" " * self.viewport_width, background)
            yield newline

        for y in range(0, image_height, 2):
            if left_padding:
                yield Segment(" " * left_padding, background)

            for x in range(image_width):
                upper = self._pixel_rgb(pixels[x, y])

                if y + 1 < image_height:
                    lower = self._pixel_rgb(pixels[x, y + 1])
                else:
                    lower = upper

                upper_color = color_cache.setdefault(upper, Color.from_rgb(*upper))
                lower_color = color_cache.setdefault(lower, Color.from_rgb(*lower))

                yield Segment("▀", Style(color=upper_color, bgcolor=lower_color))

            yield newline

    @staticmethod
    def _pixel_rgb(pixel: int | tuple[int, ...]) -> RGBColor:
        if isinstance(pixel, tuple):
            return pixel[:3]

        return (pixel, pixel, pixel)


def decode_image(raw_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(raw_bytes))
        image.load()
    except Exception as error:
        raise ValueError("Could not decode image bytes") from error

    return image


def build_renderable(
    source: Image.Image,
    viewport_width: int,
    viewport_height: int,
    options: RenderOptions,
) -> HalfBlockImage:
    fitted = prepare_image(source, viewport_width, viewport_height, options)
    return HalfBlockImage(fitted, viewport_width, viewport_height)


def prepare_image(
    source: Image.Image,
    viewport_width: int,
    viewport_height: int,
    options: RenderOptions,
) -> Image.Image:
    if viewport_width < 1 or viewport_height < 1:
        return source.convert("RGB")

    image = source.convert("RGBA")
    image = _flatten_alpha(image, options.background)

    target_width, target_height = _fit_to_viewport(
        image.size,
        viewport_width,
        viewport_height,
    )

    if image.size != (target_width, target_height):
        downscaling = target_width < image.width or target_height < image.height
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        if downscaling and options.sharpen:
            image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=2))

    return image


def _flatten_alpha(image: Image.Image, background: RGBColor) -> Image.Image:
    if image.mode != "RGBA":
        return image.convert("RGB")

    bg = Image.new("RGBA", image.size, background + (255,))
    composed = Image.alpha_composite(bg, image)
    return composed.convert("RGB")


def _fit_to_viewport(
    image_size: tuple[int, int],
    viewport_width: int,
    viewport_height: int,
) -> tuple[int, int]:
    image_width, image_height = image_size

    max_width = max(viewport_width, 1)
    max_height = max(viewport_height * 2, 1)

    width_scale = max_width / image_width
    height_scale = max_height / image_height
    scale = min(width_scale, height_scale)

    target_width = max(1, round(image_width * scale))
    target_height = max(1, round(image_height * scale))
    return target_width, target_height
