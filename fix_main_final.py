import sys

with open('main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Fix the indentation of current_price
    if 'current_price = 0.0 # 🆕 Initialize early' in line:
        new_lines.append('            current_price = 0.0 # 🆕 Initialize early to avoid UnboundLocalError\n')
    else:
        new_lines.append(line)

# Check for duplicates again
final_lines = []
skip = False
for line in new_lines:
    if 'def _build_market_context(self, quant_analysis: Dict, predict_result, market_data: Dict) -> str:' in line:
        skip = True
    if skip and 'return context' in line:
        skip = False
        continue
    if not skip:
        final_lines.append(line)

with open('main.py', 'w') as f:
    f.writelines(final_lines)

print("✅ main.py fixed with correct indentation")
