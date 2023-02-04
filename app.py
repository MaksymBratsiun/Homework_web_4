from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

SERVER_IP = ''
SERVER_PORT = 3000
SOCKET_IP = '127.0.0.1'
SOCKET_PORT = 5000
BASE_DIR = pathlib.Path()


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)

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
        m_type, *rest = mimetypes.guess_type(filename)
        if m_type:
            self.send_header('Content-type', m_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def send_data_to_socket(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (SOCKET_IP, SOCKET_PORT))


def run_server(server=HTTPServer, handler=HttpHandler):
    address = (SERVER_IP, SERVER_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    data = urllib.parse.unquote_plus(data.decode())
    try:
        incoming_data = {key: value for key, value in [el.split('=') for el in data.split('&')]}
        payload = {str(datetime.now()): incoming_data}
        with open(BASE_DIR.joinpath('storage/data.json'), 'r') as fd:
            loaded_data = json.load(fd)
        loaded_data.update(payload)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(loaded_data, fd, ensure_ascii=False)
    except ValueError as e:
        logging.error(f'Failed parse data {data} with error: {e}')
    except OSError as e:
        logging.error(f'Failed write data {data} with error: {e}')


def run_socket():
    socket_address = (SOCKET_IP, SOCKET_PORT)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(socket_address)
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    thread_server = Thread(target=run_server)
    thread_server.start()
    thread_socket = Thread(target=run_socket)
    thread_socket.start()
