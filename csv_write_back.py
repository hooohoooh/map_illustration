# -*- coding: utf-8 -*-
import csv
import os
import sys
import re

def parse_coord(coord_str):
    """将 CSV 中的坐标字符串（如 "116, -134.5"）解析为两个数值，返回格式化后的坐标字符串（如 "(116, -134.5)"）"""
    parts = coord_str.split(',')
    if len(parts) != 2:
        raise ValueError(f"无效的坐标格式: {coord_str}")
    x_str = parts[0].strip()
    y_str = parts[1].strip()
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        return f"({x_str}, {y_str})"
    x_fmt = str(int(x)) if x.is_integer() else str(x)
    y_fmt = str(int(y)) if y.is_integer() else str(y)
    return f"({x_fmt}, {y_fmt})"

def generate_parties_csv(cities_data, output_path):
    """生成 parties.csv 文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for city, coord, name, faction, faction_cn, extra in cities_data:
            line = f"p_{city}|{name}"
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def generate_module_scripts(cities_data, output_path):
    """生成 module_scripts.py 文件（仅包含 call_script 行，且仅当派系非空）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn, extra in cities_data:
            if faction:
                line = f'(call_script, "script_give_center_to_faction_aux", "p_{city}", "{faction}"),'
                f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def update_module_parties(cities_data, output_path):
    """
    更新现有的 module_parties.py 文件，替换城市代码、坐标以及末尾的额外数字。
    不会修改 icon 部分。
    """
    if not os.path.exists(output_path):
        generate_module_parties_new(cities_data, output_path)
        return

    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    city_to_index = {}
    for idx, line in enumerate(lines):
        m = re.search(r'^\s*\(\s*"([^"]+)"', line)
        if m:
            old_city = m.group(1)
            city_to_index[old_city] = idx

    updated = False
    for city, coord, name, faction, faction_cn, extra in cities_data:
        if city in city_to_index:
            idx = city_to_index[city]
            line = lines[idx]
            new_line = line

            # 替换城市代码（前两个出现）
            new_line = new_line.replace(f'"{city}"', f'"{city}"', 2)

            # 替换坐标
            new_coord_str = parse_coord(coord)
            coord_pattern = r'\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)'
            new_line = re.sub(coord_pattern, new_coord_str, new_line, count=1)

            # 替换末尾的额外数字（仅匹配 "], 数字)" 模式）
            extra_pattern = r'(,\s*\[\]\s*,\s*)\d+(\s*\))'
            if re.search(extra_pattern, new_line):
                new_line = re.sub(extra_pattern, rf'\g<1>{extra}\g<2>', new_line)

            if new_line != line:
                lines[idx] = new_line
                updated = True

    if updated:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"更新 {output_path} 完成。")
    else:
        print(f"{output_path} 中未找到任何匹配的城市，未做修改。")
        
def generate_module_parties_new(cities_data, output_path):
    """生成新的 module_parties.py 文件，根据城市类型使用正确的图标"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn, extra in cities_data:
            # 根据城市名称前缀决定图标
            if city.startswith('town'):
                icon = "icon_town|pf_town"
            elif city.startswith('castle'):
                icon = "icon_castle_a|pf_castle"
            elif city.startswith('village'):
                icon = "icon_village_a|pf_village"
            else:
                icon = "icon_town|pf_town"
            coord_str = parse_coord(coord)
            line = f'("{city}", "{city}", {icon}, no_menu, pt_none, fac_neutral, 0, ai_bhvr_hold, 0, {coord_str}, [], {extra}),'
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = 'result.csv'

    if not os.path.exists(csv_file):
        print(f"错误：找不到文件 {csv_file}")
        return

    cities_data = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 5:
                print(f"警告：第 {row_num} 行字段不足5个，跳过 {row}")
                continue

            city = row[0].strip()
            coord = row[1].strip()
            name = row[2].strip()
            faction = row[3].strip()
            faction_cn = row[4].strip()
            # 额外数字列（第6列）
            if len(row) >= 6 and row[5].strip():
                try:
                    extra = int(row[5].strip())
                except ValueError:
                    print(f"警告：第 {row_num} 行额外数字不是有效整数，使用默认值195")
                    extra = 195
            else:
                extra = 195
                if len(row) < 6:
                    print(f"提示：第 {row_num} 行缺少额外数字列，自动设置为 195")

            if city and coord:
                cities_data.append((city, coord, name, faction, faction_cn, extra))

    if not cities_data:
        print("没有有效数据，退出。")
        return

    update_module_parties(cities_data, 'module_parties.py')
    generate_parties_csv(cities_data, 'parties.csv')
    generate_module_scripts(cities_data, 'module_scripts.py')

    print("全部文件处理完成！")

if __name__ == '__main__':
    main()