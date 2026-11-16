from http.server import BaseHTTPRequestHandler
from proxy_utils import proxy_media


class handler(BaseHTTPRequestHandler):
    """Vercel endpoint /api/media?path=/image.png proxies approved media."""

    def do_GET(self):
        proxy_media(self)

    def do_HEAD(self):
        proxy_media(self)
