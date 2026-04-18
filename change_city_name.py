# -*- coding: utf-8 -*-
import csv
import sys
import os
import re

def normalize_name(name):
    """移除中文名中的所有空白字符（包括各种空格、全角空格、制表符等）"""
    return re.sub(r'\s+', '', name).replace('\u3000', '')

def get_type_prefix(code):
    """提取城市代码的类型前缀（town_、castle_、village_）"""
    if code.startswith('town_'):
        return 'town_'
    elif code.startswith('castle_'):
        return 'castle_'
    elif code.startswith('village_'):
        return 'village_'
    else:
        return None

def load_old_mapping(old_csv_path):
    """
    读取 parties_old.csv，返回映射字典：
    {规范化中文名: [(旧城市代码, 类型前缀), ...]}
    支持同一中文名对应多个不同类型代码的情况。
    """
    mapping = {}
    if not os.path.exists(old_csv_path):
        print(f"错误：找不到文件 {old_csv_path}")
        return mapping

    with open(old_csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|', 1)
            if len(parts) != 2:
                continue
            code_with_p = parts[0].strip()
            chinese_name = parts[1].strip()
            if code_with_p.startswith('p_'):
                old_code = code_with_p[2:]  # 去掉 p_ 前缀
                prefix = get_type_prefix(old_code)
                if prefix:
                    normalized = normalize_name(chinese_name)
                    # 使用 setdefault 确保键存在列表
                    mapping.setdefault(normalized, []).append((old_code, prefix))
    return mapping

def process_result_csv(input_path, old_mapping, output_path=None):
    """
    处理 result.csv：
    - 新增“旧城市代号”列，放在原城市代号之后
    - 根据中文名匹配 old_mapping，且类型前缀相同才替换
    - 若匹配成功：城市代号列变为旧代码，旧城市代号列为原代码
    - 若匹配失败：城市代号列留空，旧城市代号列为原代码
    """
    if output_path is None:
        output_path = input_path

    rows = []
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("输入文件为空。")
        return

    header = rows[0]
    try:
        city_code_idx = header.index('城市代号')
        city_name_idx = header.index('城市中文名')
    except ValueError as e:
        print("表头缺少必要列：", e)
        return

    # 构建新表头
    new_header = header[:city_code_idx+1] + ['旧城市代号'] + header[city_code_idx+1:]
    new_rows = [new_header]

    for row in rows[1:]:
        if len(row) <= max(city_code_idx, city_name_idx):
            continue

        old_city_code = row[city_code_idx].strip()
        chinese_name = row[city_name_idx].strip()
        normalized = normalize_name(chinese_name)
        original_prefix = get_type_prefix(old_city_code)

        new_city_code = ''
        saved_old_code = old_city_code

        if normalized in old_mapping and original_prefix:
            candidates = old_mapping[normalized]  # 候选列表
            # 在候选中查找前缀匹配的项
            for mapped_code, mapped_prefix in candidates:
                if original_prefix == mapped_prefix:
                    new_city_code = mapped_code
                    saved_old_code = old_city_code
                    break  # 找到第一个匹配即可

        # 构建新行
        new_row = row[:city_code_idx] + [new_city_code] + [saved_old_code] + row[city_code_idx+1:]
        new_rows.append(new_row)

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(f"处理完成，结果保存至 {output_path}")

def main():
    old_csv = 'parties_old.csv'
    result_csv = 'result.csv'
    output_csv = 'result_new.csv'  # 可改为 'result.csv' 直接覆盖

    print("加载旧版映射...")
    mapping = load_old_mapping(old_csv)
    print(f"已加载 {len(mapping)} 个中文名映射。")

    print("处理 result.csv...")
    process_result_csv(result_csv, mapping, output_csv)

if __name__ == '__main__':
    main()