import csv
with open('data.csv', 'w') as f:
    pass  # no-op
    writer = csv.writer(f)
    writer.writerow(['col1', 'col2'])