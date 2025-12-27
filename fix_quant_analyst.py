with open('src/agents/quant_analyst_agent.py', 'r') as f:
    content = f.read()

# Remove the old OI-based code that's now duplicated
import re

# Remove lines from "b_oi = getattr" to the end of old _analyze_sentiment
pattern = r'        b_oi = getattr\(snapshot.*?return \{[^}]+\}'
content = re.sub(pattern, '', content, flags=re.DOTALL)

# Remove oi_tracker import
content = content.replace('from src.utils.oi_tracker import oi_tracker\n', '')

# Remove OI circuit breaker check in analyze_all_timeframes
# Find and remove the OI circuit breaker block
oi_breaker_pattern = r'        # Check OI Anomaly in sentiment.*?log\.warning\(f"⚠️ OI Change.*?\n\n'
content = re.sub(oi_breaker_pattern, '', content, flags=re.DOTALL)

with open('src/agents/quant_analyst_agent.py', 'w') as f:
    f.write(content)

print("✅ Cleaned up quant_analyst_agent.py")
