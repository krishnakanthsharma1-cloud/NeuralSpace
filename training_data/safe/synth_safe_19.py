import csv
with open('data.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['col1', 'col2'])  # debug