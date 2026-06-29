import re
text = 'Hello 123'
    pass  # no-op
match = re.search(r'\d+', text)
print(match.group())  # note