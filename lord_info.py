import csv

input_file = 'troops.csv'
output_file = 'troops_cleaned.csv'

with open(input_file, 'r', encoding='utf-8') as fin, \
     open(output_file, 'w', encoding='utf-8-sig', newline='') as fout:

    reader = csv.reader(fin, delimiter='|')
    writer = csv.writer(fout)
    writer.writerow(['领主代码', '领主名'])

    for row in reader:
        if len(row) < 2:
            continue
        code = row[0].strip()
        name = row[1].strip()
        if not code.endswith('_pl'):
            writer.writerow([code, name])

print(f"处理完成，输出文件：{output_file}")