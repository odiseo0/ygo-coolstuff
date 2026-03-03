import asyncio

from textual import events
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget

from src.image_viewer.cache import ImageCache
from src.image_viewer.loader import HttpImageLoader, ImageLoadError
from src.image_viewer.pipeline import HalfBlockImage, RenderOptions, build_renderable, decode_image


class CardImageViewer(Widget):
    DEFAULT_CSS = """
    CardImageViewer {
        background: black;
        color: white;
    }
    """

    state: reactive[str] = reactive("idle")
    error_message: reactive[str] = reactive("")

    def __init__(
        self,
        *,
        url: str | None = None,
        loader: HttpImageLoader | None = None,
        cache: ImageCache | None = None,
        render_options: RenderOptions | None = None,
        resize_debounce_seconds: float = 0.1,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._url = url
        self._loader = loader or HttpImageLoader()
        self._cache = cache or ImageCache()
        self._render_options = render_options or RenderOptions()
        self._resize_debounce_seconds = resize_debounce_seconds

        self._revision = 0
        self._source_image_bytes: bytes | None = None
        self._frame: HalfBlockImage | None = None
        self._resize_timer: Timer | None = None

    def set_url(self, url: str) -> None:
        self._url = url.strip()

        if not self._url:
            self.clear()
            return

        self._start_load()

    def clear(self) -> None:
        self._revision += 1
        self._source_image_bytes = None
        self._frame = None
        self.state = "idle"
        self.error_message = ""
        self.refresh()

    def reload(self) -> None:
        if not self._url:
            return

        self._cache.raw_images.clear()
        self._cache.frames.clear()
        self._start_load()

    def render(self) -> str | HalfBlockImage:
        if self.state == "loading":
            return "Loading image..."

        if self.state == "error":
            return f"Could not load image\n{self.error_message}"

        if self.state == "ready" and self._frame is not None:
            return self._frame

        return "No image selected"

    def on_mount(self) -> None:
        if self._url:
            self._start_load()

    def on_resize(self, event: events.Resize) -> None:
        if self.state != "ready" or self._source_image_bytes is None:
            return

        if event.size.width < 1 or event.size.height < 1:
            return

        if self._resize_timer is not None:
            self._resize_timer.stop()

        self._resize_timer = self.set_timer(
            self._resize_debounce_seconds,
            self._rerender_from_cache,
        )

    def _start_load(self) -> None:
        if not self._url:
            return

        self._revision += 1
        revision = self._revision

        self.state = "loading"
        self.error_message = ""
        self.refresh()

        self.run_worker(
            self._load_and_render(self._url, revision),
            group="image-load",
            exclusive=True,
        )

    def _rerender_from_cache(self) -> None:
        if not self._url or self._source_image_bytes is None:
            return

        self._revision += 1
        revision = self._revision
        self.run_worker(
            self._render_from_source(self._url, self._source_image_bytes, revision),
            group="image-render",
            exclusive=True,
        )

    async def _load_and_render(self, url: str, revision: int) -> None:
        raw_bytes = self._cache.raw_images.get(url)

        if raw_bytes is None:
            try:
                raw_bytes = await self._loader.fetch(url)
            except ImageLoadError as error:
                self._show_error(revision, error.reason)
                return

            self._cache.raw_images.set(url, raw_bytes)

        await self._render_from_source(url, raw_bytes, revision)

    async def _render_from_source(self, url: str, raw_bytes: bytes, revision: int) -> None:
        width = self.size.width
        height = self.size.height

        if width < 1 or height < 1:
            return

        frame_key = (url, width, height, self._render_options.to_cache_key())
        cached = self._cache.frames.get(frame_key)

        if isinstance(cached, HalfBlockImage):
            if revision != self._revision:
                return

            self._source_image_bytes = raw_bytes
            self._frame = cached
            self.state = "ready"
            self.refresh()
            return

        try:
            frame = await asyncio.to_thread(
                self._build_frame,
                raw_bytes,
                width,
                height,
            )
        except ValueError as error:
            self._show_error(revision, str(error))
            return
        except Exception:
            self._show_error(revision, "Unexpected error while rendering image")
            return

        if revision != self._revision:
            return

        self._cache.frames.set(frame_key, frame)
        self._source_image_bytes = raw_bytes
        self._frame = frame
        self.state = "ready"
        self.refresh()

    def _build_frame(self, raw_bytes: bytes, width: int, height: int) -> HalfBlockImage:
        image = decode_image(raw_bytes)
        return build_renderable(image, width, height, self._render_options)

    def _show_error(self, revision: int, message: str) -> None:
        if revision != self._revision:
            return

        self._source_image_bytes = None
        self._frame = None
        self.state = "error"
        self.error_message = message
        self.refresh()
