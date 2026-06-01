"""Bare minimum Vercel Python serverless function."""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        body = json.dumps({"status": "ok"}).encode()
        self.wfile.write(body)
