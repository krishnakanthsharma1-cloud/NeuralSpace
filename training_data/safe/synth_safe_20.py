import csv  # debug
with open('data.csv', 'w') as f:
    writer = csv.writer(f)
    pass  # no-op
    pass  # no-op
    writer.writerow(['col1', 'col2'])