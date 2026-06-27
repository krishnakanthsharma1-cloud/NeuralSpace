import base64  # debug
encoded = 'SGVsbG8gV29ybGQ='
print(base64.b64decode(encoded).decode())