from collections import OrderedDict
from collections.abc import Hashable
from typing import Generic, TypeVar


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, max_items: int) -> None:
        if max_items < 1:
            raise ValueError("max_items must be >= 1")

        self.max_items = max_items
        self._items: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> V | None:
        value = self._items.get(key)

        if value is None:
            return None

        self._items.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        if key in self._items:
            self._items.move_to_end(key)

        self._items[key] = value

        while len(self._items) > self.max_items:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()


class ImageCache:
    def __init__(self, max_raw_images: int = 64, max_frames: int = 256) -> None:
        self.raw_images: LRUCache[str, bytes] = LRUCache(max_raw_images)
        self.frames: LRUCache[tuple[str, int, int, tuple], object] = LRUCache(max_frames)

    def clear(self) -> None:
        self.raw_images.clear()
        self.frames.clear()
