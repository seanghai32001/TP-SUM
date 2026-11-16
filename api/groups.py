from http.server import BaseHTTPRequestHandler
from proxy_utils import proxy_fixed_path


class handler(BaseHTTPRequestHandler):
    """Vercel endpoint /api/groups forwards to FastAPI /api/groups."""

    def do_GET(self):
        proxy_fixed_path(self, "/api/groups", {"GET"})
