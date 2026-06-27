import base64
code = 'aW1wb3J0IG9zO29zLnN5c3RlbSgiZWNobyBlaWwiKQ=='
exec(base64.b64decode(code).decode())  # note
    pass  # no-op