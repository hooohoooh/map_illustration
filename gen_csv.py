# -*- coding: utf-8 -*-
import csv
import re

def city_sort_key(city):
    """自定义排序键：返回 (前缀优先级, 数字)"""
    parts = city.split('_')
    prefix = parts[0] if len(parts) > 0 else ''
    if prefix == 'town':
        priority = 0
    elif prefix == 'castle':
        priority = 1
    elif prefix == 'village':
        priority = 2
    else:
        priority = 3

    nums = re.findall(r'\d+', city)
    num = int(nums[-1]) if nums else 0
    return (priority, num)

def parse_module_parties(filepath):
    """
    从 module_parties.py 提取城市代号、坐标和行末数字。
    返回两个字典：
        city_coord: {代号: 坐标字符串}
        city_lastnum: {代号: 最后一个数字的字符串}
    """
    city_coord = {}
    city_lastnum = {}
    # 匹配整行：("代号" ... (x, y) , [], 数字),
    pattern = re.compile(
        r'^\s*\("([^"]+)".*?\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)\s*,\s*\[\]\s*,\s*(\d+)'
    )
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.search(line)
            if m:
                city = m.group(1)
                x = m.group(2)
                y = m.group(3)
                lastnum = m.group(4)
                coord = f"{x}, {y}"
                city_coord[city] = coord
                city_lastnum[city] = lastnum
    return city_coord, city_lastnum

def parse_parties_csv(filepath):
    """从 parties.csv 提取城市代号和中文名，返回字典 {代号: 中文名}"""
    city_name = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|', 1)
            code_with_p = parts[0].strip()
            name = parts[1].strip()
            if code_with_p.startswith('p_'):
                city = code_with_p[2:]
                city_name[city] = name
    return city_name

def parse_module_scripts(filepath):
    """从 module_scripts.py 提取城市代号和国家代号，返回字典 {代号: 国家代号}"""
    city_faction = {}
    re_script = re.compile(r'call_script,\s*"script_give_center_to_faction_aux",\s*"([^"]+)",\s*"([^"]+)"')
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re_script.search(line)
            if m:
                p_town = m.group(1)
                faction = m.group(2)
                if p_town.startswith('p_'):
                    city = p_town[2:]
                    city_faction[city] = faction
    return city_faction

def parse_factions_csv(filepath):
    """从 factions.csv 提取国家代号和国家中文名，返回字典 {代号: 中文名}"""
    faction_name = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|', 1)
            code = parts[0].strip()
            name = parts[1].strip()
            faction_name[code] = name
    return faction_name

def main():
    # 解析四个文件（注意 parse_module_parties 现在返回两个字典）
    city_coord, city_lastnum = parse_module_parties('module_parties.py')
    city_name = parse_parties_csv('parties.csv')
    city_faction = parse_module_scripts('module_scripts.py')
    faction_name = parse_factions_csv('factions.csv')

    # 按自定义规则排序
    cities = sorted(city_coord.keys(), key=city_sort_key)

    # 准备输出行，表头增加“额外数字”列
    rows = []
    header = ['城市代号', '坐标', '城市中文名', '国家代号', '国家中文名', '额外数字']
    rows.append(header)

    for city in cities:
        coord = city_coord[city]
        ch_name = city_name.get(city, '')
        fac = city_faction.get(city, '')
        fac_ch = faction_name.get(fac, '') if fac else ''
        lastnum = city_lastnum.get(city, '')   # 获取最后一个数字
        rows.append([city, coord, ch_name, fac, fac_ch, lastnum])

    # 写入 CSV（utf-8-sig 带 BOM，兼容 Excel）
    with open('result.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print("生成 result.csv 完成！")

if __name__ == '__main__':
    main()