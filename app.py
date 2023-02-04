from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
import mimetypes
import pathlib
import socket
import urllib.parse

SERVER_IP = ''
SERVER_PORT = 3000
SOCKET_IP = ''
SOCKET_PORT = 5000
BASE_DIR = pathlib.Path()

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = urllib.parse.unquote_plus(body.decode())
        payload = {key: value for key, value in [el.split('=') for el in body.split('&')]}
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(payload, fd, ensure_ascii=False)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.sent_html('index.html')
            case '/message.html':
                self.sent_html('message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.sent_static(file)
                else:
                    self.sent_html('error.html', 404)

    def sent_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def sent_static(self, filename):
        self.send_response(200)
        m_type, *rest = mimetypes.guess_type(filename) # -> (m_type, None)
        if m_type:
            self.send_header('Content-type', m_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def run_server(server=HTTPServer, handler=HttpHandler):
    address = (SERVER_IP, SERVER_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()

def run_socket():
    pass
    # address = (SOCKET_IP, SOCKET_PORT)



if __name__ == '__main__':
    run_server()

