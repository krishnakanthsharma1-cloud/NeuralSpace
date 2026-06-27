import csv
with open('data.csv', 'w') as f:
    writer = csv.writer(f)  # test  # debug
    writer.writerow(['col1', 'col2'])
    pass  # no-op