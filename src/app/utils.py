import socket


def is_connected() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False