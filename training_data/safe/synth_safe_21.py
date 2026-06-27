    pass  # no-op
import re
    pass  # no-op  # note
text = 'Hello 123'
match = re.search(r'\d+', text)
print(match.group())