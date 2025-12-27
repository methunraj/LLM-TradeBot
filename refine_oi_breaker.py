import re

with open('src/agents/quant_analyst_agent.py', 'r') as f:
    content = f.read()

# Refine the has_sufficient_data check
# Instead of records count, check if we have data spanning at least 2 hours to be safe for a "24h change" estimation
new_check = '''        # 🆕 Check if OI tracker has sufficient data before triggering circuit breaker
        from src.utils.oi_tracker import oi_tracker
        symbol = getattr(snapshot, 'symbol', 'ETHUSDT')
        oi_stats = oi_tracker.get_stats(symbol)
        
        # Check records and time span
        num_records = oi_stats.get('records', 0)
        has_sufficient_data = False
        if num_records >= 2:
            records = oi_tracker.history.get(symbol, [])
            if records:
                time_span_hours = (records[-1]['ts'] - records[0]['ts']) / (1000 * 3600)
                has_sufficient_data = time_span_hours >= 2 # Need at least 2 hours of data to trust the trend
        
        if has_sufficient_data and oi_change > 200:
'''

# Replace the old check
content = re.sub(r'        # 🆕 Check if OI tracker has sufficient data before triggering circuit breaker.*?if has_sufficient_data and oi_change > 200:', 
                 new_check, content, flags=re.DOTALL)

with open('src/agents/quant_analyst_agent.py', 'w') as f:
    f.write(content)

print("✅ QuantAnalystAgent OI breaker refined")
