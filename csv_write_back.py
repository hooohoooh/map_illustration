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
        for city, coord, name, faction, faction_cn, extra, lord in cities_data:
            line = f"p_{city}|{name}"
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

def generate_module_scripts(cities_data, output_path):
    """生成 module_scripts.py 文件（包含 faction 和 lord 的 call_script 行，并附加中文注释）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn, extra, lord in cities_data:
            if faction:
                line_faction = f'(call_script, "script_give_center_to_faction_aux", "p_{city}", "{faction}"),'
                f.write(line_faction + '\n')
            if lord:
                line_lord = f'(call_script, "script_give_center_to_lord", "p_{city}", "{lord}", 0),'
                f.write(line_lord + '\n')
    print(f"生成 {output_path} 完成。")

def generate_module_parties_new(cities_data, output_path):
    """生成新的 module_parties.py 文件，根据城市类型使用正确的图标，并附加中文注释"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn, extra, lord in cities_data:
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
            # ---------- 修改点：根据新的列顺序读取数据 ----------
            # 新 CSV 列顺序：城市代号(0), 坐标(1), 城门朝向(2), 城市中文名(3), 国家代号(4), 国家中文名(5), 领主代码(6), 领主中文名(7)
            if len(row) < 6:  # 至少需要前6列（到国家中文名），领主代码和中文名可选
                print(f"警告：第 {row_num} 行字段不足6个，跳过 {row}")
                continue

            city = row[0].strip()
            coord = row[1].strip()
            # 城门朝向（原额外数字）位于第3列
            extra_str = row[2].strip()
            name = row[3].strip()           # 城市中文名
            faction = row[4].strip()        # 国家代号
            faction_cn = row[5].strip()     # 国家中文名

            # 处理城门朝向数值（原额外数字）
            if extra_str:
                try:
                    extra = int(extra_str)
                except ValueError:
                    print(f"警告：第 {row_num} 行城门朝向不是有效整数，使用默认值195")
                    extra = 195
            else:
                extra = 195
                print(f"提示：第 {row_num} 行缺少城门朝向，自动设置为 195")

            # 领主代码（第7列），可选
            lord = ''
            if len(row) >= 7:
                lord = row[6].strip()

            # 领主中文名（第8列）在本脚本中不使用，直接忽略，不读取

            if city and coord:
                cities_data.append((city, coord, name, faction, faction_cn, extra, lord))
        # ---------- 修改结束 ----------

    if not cities_data:
        print("没有有效数据，退出。")
        return

    # 直接覆盖生成三个文件
    generate_module_parties_new(cities_data, 'module_parties.py')
    generate_parties_csv(cities_data, 'parties.csv')
    generate_module_scripts(cities_data, 'module_scripts.py')

    print("全部文件处理完成！")

if __name__ == '__main__':
    main()