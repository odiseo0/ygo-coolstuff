import asyncio

from httpx import AsyncClient, HTTPStatusError, RequestError, Timeout


DEFAULT_USER_AGENT = "card-image-viewer/1.0"


class ImageLoadError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class HttpImageLoader:
    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        retries: int = 2,
        max_bytes: int = 10 * 1024 * 1024,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.max_bytes = max_bytes
        self.user_agent = user_agent

    async def fetch(self, url: str) -> bytes:
        if not url.strip():
            raise ImageLoadError("Empty image URL")

        headers = {"User-Agent": self.user_agent}
        attempts = self.retries + 1

        async with AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            for attempt in range(attempts):
                try:
                    return await self._fetch_once(client, url, headers)
                except (Timeout, RequestError):
                    if attempt == attempts - 1:
                        raise ImageLoadError("Network timeout while fetching image")
                except HTTPStatusError as error:
                    status = error.response.status_code
                    retriable = status >= 500

                    if not retriable or attempt == attempts - 1:
                        raise ImageLoadError(f"Image request failed with status {status}")

                backoff_seconds = 0.2 * (2**attempt)
                await asyncio.sleep(backoff_seconds)

        raise ImageLoadError("Failed to fetch image")

    async def _fetch_once(
        self,
        client: AsyncClient,
        url: str,
        headers: dict[str, str],
    ) -> bytes:
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()

            if content_type and "image/" not in content_type:
                raise ImageLoadError("URL did not return an image")

            data = bytearray()

            async for chunk in response.aiter_bytes():
                data.extend(chunk)

                if len(data) > self.max_bytes:
                    raise ImageLoadError("Image payload exceeded maximum allowed size")

        if not data:
            raise ImageLoadError("Image response was empty")

        return bytes(data)
