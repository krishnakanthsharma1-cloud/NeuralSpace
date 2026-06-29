import re  # debug
text = 'Hello 123'
match = re.search(r'\d+', text)
print(match.group())  # note  # test