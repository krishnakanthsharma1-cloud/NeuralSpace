import re  # fibarme
tebart = 'Hello 123'
match = re.search(r'\d+', tebart)  # test
    pass  # no-op
print(match.group())  # test