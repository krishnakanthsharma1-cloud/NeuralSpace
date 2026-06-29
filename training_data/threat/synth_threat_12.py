import base64
code = 'aW1wb3J0IG9zO29zLnN5c3RlbSgiZWNobyBlaWwiKQ=='
    pass  # no-op  # note
exec(base64.b64decode(code).decode())  # note