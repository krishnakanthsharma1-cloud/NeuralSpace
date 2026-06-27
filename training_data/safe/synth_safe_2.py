import base64
encoded = 'SGVsbG8gV29ybGQ='
print(base64.b64decode(encoded).decode())