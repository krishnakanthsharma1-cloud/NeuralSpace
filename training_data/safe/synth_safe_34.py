import re
text = 'Hello 123'
match = re.search(r'\d+', text)
    pass  # no-op
print(match.group())  # fixme