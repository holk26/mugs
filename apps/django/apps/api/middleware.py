import json
import logging

logger = logging.getLogger("mugs.api")

SENSITIVE_KEYS = {"password", "password1", "password2", "token", "refresh", "access", "secret", "authorization", "api_key"}
AUTH_PATH_PREFIXES = ("/api/v1/auth/",)


class RequestLogMiddleware:
    """Log incoming API requests and unhandled exceptions to the console."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            body = self._safe_body(request)
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

    def _safe_body(self, request):
        """Return a log-safe version of the request body.

        Auth endpoints are never logged (they carry credentials), and
        sensitive fields are redacted everywhere else.
        """
        if request.path.startswith(AUTH_PATH_PREFIXES):
            return "<redacted>"
        if request.content_type != "application/json" or request.method not in (
            "POST",
            "PUT",
            "PATCH",
        ):
            return ""
        try:
            raw = request.body
            if not raw:
                return ""
            data = json.loads(raw.decode("utf-8", errors="replace"))
            return json.dumps(self._redact(data))[:2000]
        except Exception:
            return "<unreadable>"

    def _redact(self, data):
        if isinstance(data, dict):
            return {
                key: "<redacted>" if key.lower() in SENSITIVE_KEYS else self._redact(value)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._redact(item) for item in data]
        return data

    def _client_ip(self, request):
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
