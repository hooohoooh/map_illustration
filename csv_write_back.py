# -*- coding: utf-8 -*-
import csv
import codecs
import os
import sys

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

def generate_module_parties(cities_data, output_path):
    """生成 module_parties.py 文件"""
    with codecs.open(output_path, 'w', encoding='utf-8') as f:
        # 可选：添加文件头注释
        f.write("# Generated from CSV data\n")
        for city, coord, name, faction, faction_cn in cities_data:
            # 确定 icon 类型
            if city.startswith('town'):
                icon = "icon_town|pf_town"
            elif city.startswith('castle'):
                icon = "icon_castle|pf_castle"
            else:
                # 默认使用 town 类型
                icon = "icon_town|pf_town"
            # 格式化坐标
            coord_str = parse_coord(coord)
            # 生成条目
            line = f'("{city}", "{city}", {icon}, no_menu, pt_none, fac_neutral, 0, ai_bhvr_hold, 0, {coord_str}, [], 195),'
            f.write(line + '\n')
    print(f"生成 {output_path} 完成。")

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
    with codecs.open(csv_file, 'r', encoding='utf-8-sig') as f:  # 使用 utf-8-sig 自动处理 BOM
        reader = csv.reader(f)
        header = next(reader)  # 跳过标题行
        # 假设列顺序为：城市代号, 坐标, 城市中文名, 国家代号, 国家中文名
        for row in reader:
            if len(row) < 5:
                print(f"警告：跳过无效行 {row}")
                continue
            city = row[0].strip()
            coord = row[1].strip()
            name = row[2].strip()
            faction = row[3].strip()
            faction_cn = row[4].strip()
            if city and coord:  # 城市代号和坐标必须存在
                cities_data.append((city, coord, name, faction, faction_cn))
    
    if not cities_data:
        print("没有有效数据，退出。")
        return

    # 生成三个文件
    generate_module_parties(cities_data, 'module_parties.py')
    generate_parties_csv(cities_data, 'parties.csv')
    generate_module_scripts(cities_data, 'module_scripts.py')

    print("全部文件生成完成！")

if __name__ == '__main__':
    main()