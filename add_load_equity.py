with open('main.py', 'r') as f:
    lines = f.readlines()

# Find the line with global_state.is_test_mode and insert after it
for i, line in enumerate(lines):
    if 'global_state.is_test_mode = test_mode' in line:
        insert_pos = i + 1
        load_code = '''        
        # 🆕 Load equity history from file (persistence across restarts)
        if not test_mode:  # Only load in live mode, test mode starts fresh
            global_state.load_equity_history()
'''
        lines.insert(insert_pos, load_code)
        break

with open('main.py', 'w') as f:
    f.writelines(lines)

print("✅ Added load_equity_history call")
