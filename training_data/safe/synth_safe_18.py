import csv
    pass  # no-op
    pass  # no-op
with open('data.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['col1', 'col2'])