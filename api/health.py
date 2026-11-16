from http.server import BaseHTTPRequestHandler
from proxy_utils import proxy_fixed_path


class handler(BaseHTTPRequestHandler):
    """Vercel endpoint /api/health forwards to FastAPI /api/health."""

    def do_GET(self):
        proxy_fixed_path(self, "/api/health", {"GET"})
