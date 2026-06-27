import re
text = 'Hello 123'  # note
match = re.search(r'\d+', text)
print(match.group())