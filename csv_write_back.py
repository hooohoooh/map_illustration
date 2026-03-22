# -*- coding: utf-8 -*-
import csv
import codecs
import os
import sys
import re

def parse_coord(coord_str):
    """将 CSV 中的坐标字符串（如 "116, -134.5"）解析为两个数值，返回格式化后的坐标字符串（如 "116, -134.5"）"""
    parts = coord_str.split(',')
    if len(parts) != 2:
        raise ValueError(f"无效的坐标格式: {coord_str}")
    x_str = parts[0].strip()
    y_str = parts[1].strip()
    # 转换为数字以便格式化（整数不带小数点，浮点数保留）
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        # 如果转换失败，直接使用原始字符串（如意外情况）
        return f"({x_str}, {y_str})"
    # 格式化：整数不显示小数点
    x_fmt = str(int(x)) if x.is_integer() else str(x)
    y_fmt = str(int(y)) if y.is_integer() else str(y)
    return f"({x_fmt}, {y_fmt})"

def generate_parties_csv(cities_data, output_path):
    """生成 parties.csv 文件"""
    with codecs.open(output_path, 'w', encoding='utf-8') as f:
        for city, coord, name, faction, faction_cn in cities_data:
            line = f"p_{city}|{name}"
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def generate_module_scripts(cities_data, output_path):
    """生成 module_scripts.py 文件（仅包含 call_script 行）"""
    with codecs.open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn in cities_data:
            # 只有国家代号非空时才生成条目
            if faction:
                line = f'(call_script, "script_give_center_to_faction_aux", "p_{city}", "{faction}"),'
                f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def update_module_parties(cities_data, output_path):
    """
    更新现有的 module_parties.py 文件，仅替换每个城市的城市代码和坐标。
    如果文件不存在，则按原逻辑生成新文件。
    """
    if not os.path.exists(output_path):
        generate_module_parties_new(cities_data, output_path)
        return

    # 读取现有文件
    with codecs.open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 建立城市代码 -> 行索引的映射（根据第一个引号内的城市代码）
    city_to_index = {}
    for idx, line in enumerate(lines):
        m = re.search(r'^\s*\(\s*"([^"]+)"', line)
        if m:
            old_city = m.group(1)
            city_to_index[old_city] = idx

    updated = False
    for city, coord, name, faction, faction_cn in cities_data:
        # 查找文件中对应的行（城市代码匹配）
        if city in city_to_index:
            idx = city_to_index[city]
            line = lines[idx]
            new_line = line

            # 1. 替换城市代码（前两个出现）
            # 使用 replace 替换前两个引号内的城市代码（确保不改变周围空格）
            # 注意：如果新城市代码与旧相同，这一步不会改变任何内容
            new_line = new_line.replace(f'"{city}"', f'"{city}"', 2)

            # 2. 替换坐标
            # 解析新坐标字符串（格式如 "(116, -134.5)"）
            new_coord_str = parse_coord(coord)
            # 匹配原行中的坐标部分（第一个括号对，包含两个数字）
            coord_pattern = r'\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)'
            new_line = re.sub(coord_pattern, new_coord_str, new_line, count=1)

            if new_line != line:
                lines[idx] = new_line
                updated = True

    if updated:
        with codecs.open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"更新 {output_path} 完成。")
    else:
        print(f"{output_path} 中未找到任何匹配的城市，未做修改。")
        
def generate_module_parties_new(cities_data, output_path):
    """生成新的 module_parties.py 文件（旧逻辑）"""
    with codecs.open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn in cities_data:
            # 确定 icon 类型
            if city.startswith('town'):
                icon = "icon_town|pf_town"
            elif city.startswith('castle'):
                icon = "icon_castle|pf_castle"
            else:
                icon = "icon_town|pf_town"
            coord_str = parse_coord(coord)
            line = f'("{city}", "{city}", {icon}, no_menu, pt_none, fac_neutral, 0, ai_bhvr_hold, 0, {coord_str}, [], 195),'
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def main():
    # 从命令行参数获取输入 CSV 文件，默认为 result.csv
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = 'result.csv'
    
    if not os.path.exists(csv_file):
        print(f"错误：找不到文件 {csv_file}")
        return

    # 读取 CSV 数据
    cities_data = []
    with codecs.open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过标题行
        for row in reader:
            if len(row) < 5:
                print(f"警告：跳过无效行 {row}")
                continue
            city = row[0].strip()
            coord = row[1].strip()
            name = row[2].strip()
            faction = row[3].strip()
            faction_cn = row[4].strip()
            if city and coord:
                cities_data.append((city, coord, name, faction, faction_cn))
    
    if not cities_data:
        print("没有有效数据，退出。")
        return

    # 更新 module_parties.py（若不存在则生成）
    update_module_parties(cities_data, 'module_parties.py')
    # 生成另外两个文件
    generate_parties_csv(cities_data, 'parties.csv')
    generate_module_scripts(cities_data, 'module_scripts.py')

    print("全部文件处理完成！")

if __name__ == '__main__':
    main()