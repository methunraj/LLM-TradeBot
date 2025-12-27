with open('src/agents/data_sync_agent.py', 'r') as f:
    content = f.read()

# Fix the malformed tasks list - remove the orphaned "loop.run_in_executor(None,]" line
import re

# Find and fix the broken executor call
pattern = r'loop\.run_in_executor\(\s+None,\s+\]'
content = re.sub(pattern, '', content)

# Also fix the await line to not expect b_oi
content = content.replace(
    'k5m, k15m, k1h, q_data, b_funding, b_oi = await asyncio.gather(*tasks)',
    'k5m, k15m, k1h, q_data, b_funding = await asyncio.gather(*tasks)'
)

with open('src/agents/data_sync_agent.py', 'w') as f:
    f.write(content)

print("✅ Fixed data_sync_agent.py")
