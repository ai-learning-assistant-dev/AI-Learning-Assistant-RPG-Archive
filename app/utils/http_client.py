from typing import Optional

from aiohttp import ClientSession, ClientTimeout

http_client: Optional[ClientSession] = None


def init_http_client():
    global http_client
    http_client = ClientSession(timeout=ClientTimeout(total=60, connect=10, sock_read=10))


def get_http_client() -> ClientSession:
    """Get the HTTP client instance."""
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Call init_http_client() first.")
    return http_client
