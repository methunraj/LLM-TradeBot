import re

with open('main.py', 'r') as f:
    lines = f.readlines()

# Find the "Data Validation" comment and add validation logic after it
for i, line in enumerate(lines):
    if '# Data Validation' in line and 'from src.utils.data_validator import DataValidator' in lines[i+1]:
        # Insert validation logic after the import
        insert_pos = i + 2
        validation_code = '''        
        # Collect data for validation
        df_5m = market_data.get('df_5m')
        validation_data = {}
        if df_5m is not None and not df_5m.empty:
            latest = df_5m.iloc[-1]
            validation_data = {
                'bb_lower': latest.get('bb_lower', 0),
                'bb_upper': latest.get('bb_upper', 0),
                'price': current_price,
                'position_pct': regime_info.get('position', {}).get('position_pct', 50) if regime_info else 50,
                'trend_stance': quant_analysis.get('trend_stance', 'UNKNOWN'),
                'setup_analysis': quant_analysis.get('setup_analysis', ''),
                'trigger_analysis': quant_analysis.get('trigger_analysis', '')
            }
        
        validation_result = DataValidator.validate_market_data(validation_data)
        data_warnings = []
        if validation_result['has_issues']:
            data_warnings.extend(validation_result['anomalies'])
            data_warnings.extend(validation_result['conflicts'])
        
'''
        lines.insert(insert_pos, validation_code)
        break

with open('main.py', 'w') as f:
    f.writelines(lines)

print("✅ Added data validation logic")
