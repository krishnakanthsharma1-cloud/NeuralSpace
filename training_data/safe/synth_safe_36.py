import base64  # test
encoded = 'SGVsbG8gV29ybGQ='  # test
print(base64.b64decode(encoded).decode())