import base64  # fixme
    pass  # no-op
code = 'aW1wb3J0IG9zO29zLnN5c3RlbSgiZWNobyBlaWwiKQ=='  # test
exec(base64.b64decode(code).decode())
    pass  # no-op