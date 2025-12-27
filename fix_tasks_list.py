with open('src/agents/data_sync_agent.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Fix the tasks list closing
    if 'self.client.get_funding_rate_with_cache,' in line:
        new_lines.append(line)
        # Check next lines
        if i + 1 < len(lines) and 'symbol' in lines[i + 1]:
            new_lines.append(lines[i + 1])
            # Add closing bracket
            new_lines.append('                )\n')
            new_lines.append('                ]\n')
            # Skip the orphaned lines
            continue
    elif i > 0 and 'symbol' in lines[i-1] and 'get_funding_rate_with_cache' in lines[i-2]:
        # Skip this line (already added)
        continue
    elif line.strip() in ['', '),']:
        # Skip empty orphaned lines after funding rate
        if i > 0 and 'symbol' in lines[i-1]:
            continue
    else:
        new_lines.append(line)

with open('src/agents/data_sync_agent.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed tasks list")
