with open('src/agents/data_sync_agent.py', 'r') as f:
    lines = f.readlines()

# Find and fix the syntax error around line 184
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    
    # Remove orphaned "None," lines
    if line.strip() in ['None,', 'None,]', '],']:
        continue
    
    # Fix tasks list if it has syntax issues
    if 'tasks = [' in line:
        # Find the closing bracket
        j = i + 1
        task_lines = [line]
        while j < len(lines) and ']' not in lines[j]:
            if lines[j].strip() and lines[j].strip() not in ['None,']:
                task_lines.append(lines[j])
            j += 1
        if j < len(lines):
            task_lines.append(lines[j])  # Add closing bracket
        
        # Write corrected task list
        new_lines.extend(task_lines)
        
        # Skip processed lines
        for _ in range(j - i):
            if i + 1 < len(lines):
                lines.pop(i + 1)
        continue
    
    new_lines.append(line)

with open('src/agents/data_sync_agent.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed data_sync_agent.py syntax")
