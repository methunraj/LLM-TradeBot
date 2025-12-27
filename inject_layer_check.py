import re

with open('main.py', 'r') as f:
    content = f.read()

# Find _build_market_context and inject at start
pattern = r'(def _build_market_context\(self, quant_analysis: Dict, predict_result, market_data: Dict, regime_info: Dict = None, position_info: Dict = None\) -> str:\s+""".+?"""\s+)'

injection = r'''\1# 🚨 LAYER BLOCK PRE-CHECK (Hard Constraint)
        four_layer_status = quant_analysis.get('four_layer_result', {})
        if not four_layer_status.get('layer1_pass', True) or not four_layer_status.get('layer2_pass', True):
            reason = four_layer_status.get('blocking_reason', 'Unknown')
            return f"⛔ LAYERS 1-2 BLOCKED: {reason}\\n\\nHARD CONSTRAINT VIOLATED. Output: WAIT.\\n\\nReasoning: Four-Layer Strategy blocks this trade. All other signals irrelevant."
        
        # Data Validation
        from src.utils.data_validator import DataValidator
        
        '''

content = re.sub(pattern, injection, content, count=1, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Injected Layer block pre-check")
