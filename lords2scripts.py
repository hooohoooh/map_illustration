#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import os

def get_input_file():
    if len(sys.argv) >= 2:
        return sys.argv[1]
    else:
        # 交互式输入
        path = input("请输入 CSV 文件路径: ").strip()
        if not path:
            print("未输入路径，退出。")
            sys.exit(1)
        return path

def read_csv_safe(filepath):
    """尝试多种编码读取 CSV，返回 (列名列表, 行列表)"""
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                # 读取第一行判断列名
                sample = f.readline()
                if not sample:
                    print("文件为空。")
                    return None, None
                f.seek(0)
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    return reader.fieldnames, rows
                else:
                    print(f"使用编码 {enc} 读取成功，但没有数据行（仅有标题行？）")
                    return reader.fieldnames, []
        except (UnicodeDecodeError, csv.Error):
            continue
    print("无法用常见编码解析该文件，请检查文件格式。")
    return None, None

def main():
    input_csv = get_input_file()
    if not os.path.exists(input_csv):
        print(f"错误：文件 '{input_csv}' 不存在。")
        sys.exit(1)

    fieldnames, rows = read_csv_safe(input_csv)
    if fieldnames is None:
        sys.exit(1)

    print(f"检测到列名: {fieldnames}")
    print(f"读取到 {len(rows)} 条数据行。")

    # 检查必须的列是否存在
    required = ['领主代码', '人物', '戊辰战争时年龄']
    missing = [col for col in required if col not in fieldnames]
    if missing:
        print(f"错误：CSV 缺少以下列: {missing}")
        print("请确保列名与示例完全一致（包括全角/半角字符）。")
        sys.exit(1)

    # 生成 troops.csv
    troops_output = "troops.csv"
    with open(troops_output, 'w', encoding='utf-8', newline='') as f:
        for row in rows:
            code = row.get('领主代码', '').strip()
            name = row.get('人物', '').strip()
            if not code or not name:
                continue
            f.write(f"{code}|{name}\n")
            f.write(f"{code}_pl|{name}\n")
    print(f"已生成 {troops_output}")

    # 生成 lords_age.txt
    age_output = "lords_age.txt"
    with open(age_output, 'w', encoding='utf-8') as f:
        for row in rows:
            code = row.get('领主代码', '').strip()
            age = row.get('戊辰战争时年龄', '').strip()
            if not code or not age:
                continue
            f.write("\t\t(else_try),\n")
            f.write(f"\t\t\t(eq, \":cur_troop\", \"{code}\"),\n")
            f.write(f"\t\t\t(assign, \":age\", {age}),\n")
    print(f"已生成 {age_output}")

if __name__ == "__main__":
    main()