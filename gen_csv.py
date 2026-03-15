# -*- coding: utf-8 -*-
import csv
import re
import codecs

def city_sort_key(city):
    """自定义排序键：返回 (前缀优先级, 数字)，town 优先级0，castle优先级1"""
    # 提取前缀（第一个下划线之前的部分）
    parts = city.split('_')
    prefix = parts[0] if len(parts) > 0 else ''
    # 优先级定义
    priority = 0 if prefix == 'town' else 1 if prefix == 'castle' else 2
    # 提取最后一个数字（假设城市代号格式为 "town_123" 或 "castle_45"）
    nums = re.findall(r'\d+', city)
    if nums:
        num = int(nums[-1])
    else:
        num = 0
    return (priority, num)

def parse_module_parties(filepath):
    """从 module_parties.py 提取城市代号和坐标，返回字典 {代号: 坐标字符串}"""
    city_coord = {}
    re_city = re.compile(r'^\s*\("([^"]+)"')
    re_coord = re.compile(r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)')
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m_city = re_city.search(line)
            if not m_city:
                continue
            city = m_city.group(1)
            m_coord = re_coord.search(line)
            if m_coord:
                coord = '%s, %s' % (m_coord.group(1), m_coord.group(2))
                city_coord[city] = coord
    return city_coord

def parse_parties_csv(filepath):
    """从 parties.csv 提取城市代号和中文名，返回字典 {代号: 中文名}"""
    city_name = {}
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
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
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
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
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
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
    # 解析四个文件
    city_coord = parse_module_parties('module_parties.py')
    city_name = parse_parties_csv('parties.csv')
    city_faction = parse_module_scripts('module_scripts.py')
    faction_name = parse_factions_csv('factions.csv')

    # 按自定义规则排序：先 town 后 castle，每组内按数字升序
    cities = sorted(city_coord.keys(), key=city_sort_key)

    # 准备输出行
    rows = []
    header = ['城市代号', '坐标', '城市中文名', '国家代号', '国家中文名']
    rows.append(header)

    for city in cities:
        coord = city_coord[city]
        ch_name = city_name.get(city, '')
        fac = city_faction.get(city, '')
        fac_ch = faction_name.get(fac, '') if fac else ''
        rows.append([city, coord, ch_name, fac, fac_ch])

    # 写入带 BOM 的 UTF-8 CSV，以便 Excel 正常打开
    with open('result.csv', 'wb') as f:
        f.write(codecs.BOM_UTF8)
        writer = csv.writer(f)
        for row in rows:
            encoded_row = [cell.encode('utf-8') if isinstance(cell, unicode) else str(cell) for cell in row]
            writer.writerow(encoded_row)

    print u"生成 result.csv 完成！"

if __name__ == '__main__':
    main()