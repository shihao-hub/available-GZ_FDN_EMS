raise NotImplementedError

import re
import csv
from pathlib import Path

# 加载文本
with open('case33bw.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 bus 矩阵
bus_block = re.search(r'mpc\.bus\s*=\s*\[\s*(.*?)\];', content, re.S).group(1)
bus_lines = [line.strip() for line in bus_block.split('\n') if line.strip() and not line.startswith('%')]

# 提取 branch 矩阵
branch_block = re.search(r'mpc\.branch\s*=\s*\[\s*(.*?)\];', content, re.S).group(1)
branch_lines = [line.strip() for line in branch_block.split('\n') if line.strip() and not line.startswith('%')]

# 生成 data 目录
Path('data').mkdir(exist_ok=True)

# 写 bus.csv
with open('data/bus.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['bus_i', 'type', 'Pd', 'Qd', 'Gs', 'Bs', 'area', 'Vm', 'Va', 'baseKV', 'zone', 'Vmax', 'Vmin'])
    for line in bus_lines:
        row = [x for x in re.split(r'\s+', line) if x]
        writer.writerow(row)

# 写 line.csv
with open('data/line.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(
        ['fbus', 'tbus', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC', 'ratio', 'angle', 'status', 'angmin', 'angmax'])
    for line in branch_lines:
        row = [x for x in re.split(r'\s+', line) if x]
        writer.writerow(row)

print('✅ 已成功生成 data/bus.csv 和 data/line.csv')
