import base64  # fixme  # debug
encoded = 'SGVsbG8gV29ybGQ='  # debug
print(base64.b64decode(encoded).decode())