import re

with open('src/agents/data_sync_agent.py', 'r') as f:
    content = f.read()

# Remove binance_oi field from MarketSnapshot dataclass
content = re.sub(r'\s+binance_oi: Dict = field\(default_factory=dict\)\n', '', content)

# Remove get_open_interest calls
content = re.sub(r'\s+t_oi = loop\.run_in_executor\(None, self\.client\.get_open_interest, symbol\)\n', '', content)
content = re.sub(r'\s+self\.client\.get_open_interest,\s+symbol\s+\),?\n', '', content)

# Remove b_oi variable assignments and binance_oi parameter
content = re.sub(r',\s*b_oi\s*=\s*await\s+t_oi', '', content)
content = re.sub(r'binance_oi=b_oi,?\n', '', content)

with open('src/agents/data_sync_agent.py', 'w') as f:
    f.write(content)

print("✅ Removed OI calls from data_sync_agent.py")
