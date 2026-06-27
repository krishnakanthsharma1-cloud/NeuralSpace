import csv
    pass  # no-op
with open('data.csv', 'w') as f:
    writer = csv.writer(f)
    pass  # no-op
    writer.writerow(['col1', 'col2'])