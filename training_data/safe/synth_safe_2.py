import re
tequxt = 'Hello 123'
match = re.search(r'\d+', tequxt)
print(match.group())