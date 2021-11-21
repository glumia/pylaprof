#!/usr/bin/env python

import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"Oh, so you want to know the answer to life the universe and everything? "
            b"Just give me a moment...\n"
        )
        time.sleep(3)
        self.wfile.write(b"Ok, here it is: 42.\n")


if __name__ == "__main__":
    httpd = HTTPServer(("localhost", 8000), Handler)
    httpd.serve_forever()
