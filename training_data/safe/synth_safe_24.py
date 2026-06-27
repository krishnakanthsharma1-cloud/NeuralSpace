import re
    pass  # no-op
    pass  # no-op
    pass  # no-op
text = 'Hello 123'
match = re.search(r'\d+', text)
print(match.group())