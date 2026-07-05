"""Analyze the new JSON data file with corrected company types."""
import json

with open('data/公司的完整作品及对应制作类型.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = 0
companies = 0
mixed = []
type_counts = {"2D": 0, "3D": 0, "三渲二": 0, "混合型": 0}

for comp_name, works in data.items():
    companies += 1
    total += len(works)
    types = set(w['type'] for w in works)
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1
    if len(types) > 1:
        mixed.append((comp_name, types, len(works)))

print(f"Companies: {companies}")
print(f"Total works: {total}")
print(f"Mixed-type companies: {len(mixed)}")
for name, types, count in mixed:
    print(f"  {name}: {sorted(types)} ({count} works)")

# Check for the mentioned typo (中国奇谭)
print("\n'中国奇谭' works:")
for comp_name, works in data.items():
    for w in works:
        if '中国奇谭' in w['name']:
            print(f"  {comp_name}: {w['name']} ({w['type']})")
