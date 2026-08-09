"""HTTP/data-source client for the Daraz data source.

This module knows *how to talk to the data source* but nothing about what the
data means. It handles auth headers, request construction, response status
codes, retry logic and rate limiting, and returns raw dictionaries.

Because Daraz has no public research API, the default implementation
(``DARAZ_SOURCE_MODE=mock``) serves deterministic fake data from
``mock_source``. Swapping to a real integration only ever requires changing
this one module -- nothing else in the system changes (architecture Problem 1).
"""
from __future__ import annotations

from config import settings
from integrations import rate_limiter
from utils.logger import get_logger

log = get_logger("integrations.daraz_client")


# --------------------------------------------------------------------------
# Custom exceptions
# --------------------------------------------------------------------------
class DarazClientError(Exception):
    """Base class for data-source errors."""


class RateLimitedError(DarazClientError):
    """Raised when the source rejects us for sending too many requests."""


class NotFoundError(DarazClientError):
    """Raised when the requested resource is not found (404)."""


class ServerError(DarazClientError):
    """Raised when the source returns a 5xx error."""


class AuthError(DarazClientError):
    """Raised on authentication failures (401/403)."""


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------
class DarazClient:
    """Thin client over the configured data source."""

    def __init__(self, config: dict | None = None):
        self.config = config or settings.get_api_config()
        self.mode = self.config["mode"]
        if self.mode == "http":
            import requests  # deferred import keeps the mock path dependency-free
            self._session = requests.Session()
            self._requests = requests
        else:
            self._session = None

    # -- public API -------------------------------------------------------
    def search_products(self, keyword: str, page: int = 1, page_size: int | None = None) -> dict:
        """Search the source for products. Returns a raw dict response."""
        page_size = page_size or self.config.get("max_results", 20)
        rate_limiter.wait_if_needed()
        try:
            if self.mode == "http":
                data = self._http_search(keyword, page, page_size)
            else:
                from integrations import mock_source
                data = mock_source.search_products(keyword, page, page_size)
        finally:
            rate_limiter.record_request()
        return data

    def get_product_detail(self, product_id: str) -> dict:
        """Fetch detailed data for a product by its Daraz ID."""
        rate_limiter.wait_if_needed()
        try:
            if self.mode == "http":
                return self._http_get(f"/products/{product_id}.html")
            # Mock: synthesize a detail dict from a fresh search hit.
            from integrations import mock_source
            resp = mock_source.search_products(product_id[:8], page_size=1)
            products = resp.get("data", [])
            for p in products:
                if p.get("item_id") == product_id:
                    return p
            raise NotFoundError(f"Product {product_id} not found")
        finally:
            rate_limiter.record_request()

    def get_product_sellers(self, product_id: str) -> list[dict]:
        """Fetch seller information for a product if the source provides it."""
        rate_limiter.wait_if_needed()
        try:
            if self.mode == "http":
                resp = self._http_get(f"/products/{product_id}/sellers")
                return resp.get("sellers", [])
            from integrations import mock_source
            return mock_source.get_product_sellers(product_id)
        finally:
            rate_limiter.record_request()

    # -- private HTTP helpers (http mode only) ----------------------------
    def _http_search(self, keyword: str, page: int, page_size: int) -> dict:
        resp = self._session.get(
            f"{self.config['base_url']}/search",
            params={"q": keyword, "page": page, "limit": page_size},
            headers=self._build_headers(),
            timeout=self.config["timeout"],
        )
        self._handle_response_error(resp)
        return resp.json()

    def _http_get(self, path: str) -> dict:
        resp = self._session.get(
            f"{self.config['base_url']}{path}",
            headers=self._build_headers(),
            timeout=self.config["timeout"],
        )
        self._handle_response_error(resp)
        return resp.json()

    def _build_headers(self) -> dict:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ProductHunter/1.0)"}
        if self.config.get("api_key"):
            headers["Authorization"] = f"Bearer {self.config['api_key']}"
        return headers

    def _handle_response_error(self, response) -> None:
        """Map HTTP status codes to our custom exceptions."""
        status = getattr(response, "status_code", None)
        if status is None:
            return
        if status == 429:
            raise RateLimitedError("Data source rate-limited us (429).")
        if status == 404:
            raise NotFoundError("Resource not found (404).")
        if status in (401, 403):
            raise AuthError("Authentication with the data source failed.")
        if status >= 500:
            raise ServerError(f"Data source server error ({status}).")
        if status >= 400:
            raise DarazClientError(f"Unexpected HTTP error ({status}).")


# A single shared client instance for the application.
_client: DarazClient | None = None


def get_client() -> DarazClient:
    """Return the shared DarazClient (lazy singleton)."""
    global _client
    if _client is None:
        _client = DarazClient()
    return _client


def reset_client() -> None:
    """Drop the cached client (useful for tests/configuration changes)."""
    global _client
    _client = None
