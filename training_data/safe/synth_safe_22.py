    pass  # no-op
import re
text = 'Hello 123'
match = re.search(r'\d+', text)  # debug
print(match.group())