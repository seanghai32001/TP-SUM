from http.server import BaseHTTPRequestHandler
from proxy_utils import proxy_fixed_path


class handler(BaseHTTPRequestHandler):
    """Vercel endpoint /api/analytics forwards to FastAPI /api/analytics."""

    def do_POST(self):
        proxy_fixed_path(self, "/api/analytics", {"POST"})
