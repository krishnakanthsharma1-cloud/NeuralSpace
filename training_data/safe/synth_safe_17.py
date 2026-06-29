import csv
with open('qux.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['col1', 'col2'])  # test