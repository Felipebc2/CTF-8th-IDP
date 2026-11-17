import json
import socket
import struct

MAX_PACKET_SIZE = 65536


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise ConnectionError("connection closed")
        data += part
    return data


def recv_packet(sock):
    size = struct.unpack(">I", recv_exact(sock, 4))[0]
    if size > MAX_PACKET_SIZE:
        raise ValueError("packet too large")
    return json.loads(recv_exact(sock, size))


def send_packet(sock, value):
    data = json.dumps(value, separators=(",", ":")).encode()
    sock.sendall(struct.pack(">I", len(data)) + data)


def connect(host, port, timeout=10):
    connection = socket.create_connection((host, port), timeout=timeout)
    connection.settimeout(timeout)
    return connection
