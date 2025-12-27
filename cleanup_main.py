import re

with open('main.py', 'r') as f:
    content = f.read()

# 1. Initialize current_price early in run_trading_cycle
content = content.replace('global_state.add_log(f"📊 [{self.current_symbol}] Starting analysis...")', 
                          'global_state.add_log(f"📊 [{self.current_symbol}] Starting analysis...")\n        current_price = 0.0 # 🆕 Initialize early to avoid UnboundLocalError')

# 2. Handle duplicate _build_market_context
# The one at 1621 is the old one (shorter signature)
pattern_old = r'    def _build_market_context\(self, quant_analysis: Dict, predict_result, market_data: Dict\) -> str:.*?        return context'
content = re.sub(pattern_old, '', content, flags=re.DOTALL)

# 3. Add circuit breaker check to run_trading_cycle
# Find where quant_analysis is called: quant_analysis = await self.quant_analyst.analyze_all_timeframes(market_snapshot)
content = content.replace('quant_analysis = await self.quant_analyst.analyze_all_timeframes(market_snapshot)',
                          'quant_analysis = await self.quant_analyst.analyze_all_timeframes(market_snapshot)\n            \n            # 🚨 Handle Circuit Breaker\n            if quant_analysis.get(\'circuit_breaker_triggered\'):\n                log.warning(f"⚠️ Circuit Breaker Active: {quant_analysis.get(\'reason\')}")\n                global_state.add_log(f"❌ Circuit Breaker: {quant_analysis.get(\'reason\')}")\n                return {\'status\': \'blocked\', \'action\': \'hold\', \'details\': {\'reason\': quant_analysis.get(\'reason\')}}\n')

with open('main.py', 'w') as f:
    f.write(content)

print("✅ main.py cleaned and circuit breaker handling added")
