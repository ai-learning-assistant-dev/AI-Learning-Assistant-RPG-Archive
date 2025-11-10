"""
Request ID middleware for FastAPI application.
"""

import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store request ID across the request lifecycle
request_id_context_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_context_var.get("")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header to requests and responses."""

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generate_request_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ):
        super().__init__(app)
        self.header_name = header_name
        self.generate_request_id = generate_request_id

    async def dispatch(self, request: Request, call_next):
        """Process the request and add request ID."""
        # Get request ID from header or generate a new one
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = self.generate_request_id()

        # Set request ID in context
        request_id_context_var.set(request_id)

        # Add request ID to request state for easy access
        request.state.request_id = request_id

        try:
            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[self.header_name] = request_id

            return response
        except Exception as e:
            # Ensure request ID is in context even if an exception occurs
            request_id_context_var.set(request_id)
            raise e
