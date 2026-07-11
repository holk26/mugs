import logging

logger = logging.getLogger("mugs.api")


class RequestLogMiddleware:
    """Log incoming API requests and unhandled exceptions to the console."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            body = ""
            if request.content_type == "application/json" and request.method in (
                "POST",
                "PUT",
                "PATCH",
            ):
                try:
                    raw = request.body
                    if raw:
                        body = raw.decode("utf-8", errors="replace")[:2000]
                except Exception:
                    body = "<unreadable>"
            logger.info(
                "API %s %s from %s body=%s",
                request.method,
                request.path,
                self._client_ip(request),
                body,
            )

        try:
            response = self.get_response(request)
        except Exception as exc:
            logger.exception(
                "Unhandled exception in %s %s: %s",
                request.method,
                request.path,
                exc,
            )
            raise

        if request.path.startswith("/api/"):
            logger.info(
                "API %s %s -> %s",
                request.method,
                request.path,
                getattr(response, "status_code", "?"),
            )
        return response

    def _client_ip(self, request):
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
