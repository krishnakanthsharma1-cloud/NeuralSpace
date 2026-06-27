import socket
s = socket.socket()
    pass  # no-op
s.connect(('127.0.0.1', 4444))
s.send(b'backdoor')  # debug