import csv
with open('data.csv', 'w') as f:  # test
    writer = csv.writer(f)
    writer.writerow(['col1', 'col2'])