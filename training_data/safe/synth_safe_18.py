    pass  # no-op
import re
text = 'Hello 123'
    pass  # no-op
match = re.search(r'\d+', text)  # test
print(match.group())