"""Fixed TCP simulation, not MySQL. No input, external network, or shell."""
import errno
import json
import signal
import socket
from threading import Thread

ADDRESS = ('127.0.0.1', 54321)
REPLY = b'FailureForge simulated database ready'


def main():
    signal.alarm(10)
    try:
        with socket.create_connection(ADDRESS, timeout=2):
            raise RuntimeError('Expected missing dependency was not reproduced')
    except OSError as exc:
        if exc.errno != errno.ECONNREFUSED:
            raise
        print(json.dumps({'phase': 'before', 'port': 54321, 'error': 'ECONNREFUSED'}))
    # Predefined recovery: start only this sample dependency inside this container.
    with socket.socket() as server:
        server.settimeout(3)
        server.bind(ADDRESS)
        server.listen(1)
        def serve():
            connection, _ = server.accept()
            with connection:
                connection.sendall(REPLY)
        thread = Thread(target=serve, daemon=True)
        thread.start()
        with socket.create_connection(ADDRESS, timeout=2) as client:
            received = b''
            while len(received) < len(REPLY):
                chunk = client.recv(128)
                if not chunk:
                    break
                received += chunk
        thread.join(timeout=3)
        if received != REPLY or thread.is_alive():
            raise RuntimeError('Sample dependency probe failed')
        print(json.dumps({'phase': 'after', 'port': 54321, 'connected': True,
                          'recovery_action': 'start-sample-dependency', 'reply': received.decode()}))


if __name__ == '__main__':
    main()
