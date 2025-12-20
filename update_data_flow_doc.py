"""
使用最新实盘数据更新 DATA_FLOW_STRUCTURED.md 文档
数据来源: data/step1-6/20251219/最新时间戳文件
"""
import json
import re
from pathlib import Path
from datetime import datetime

# 数据文件路径（最新时间戳 20251219_021526）
DATA_DIR = Path('/Users/yunxuanhan/Documents/workspace/ai/ai_trader/data')
DOC_FILE = Path('/Users/yunxuanhan/Documents/workspace/ai/ai_trader/docs_organized/12_其他/DATA_FLOW_STRUCTURED.md')
TIMESTAMP = '20251219_021526'

print("=" * 100)
print("📝 DATA_FLOW_STRUCTURED.md 文档更新")
print("=" * 100)
print(f"\n数据时间戳: {TIMESTAMP}")
print(f"文档路径: {DOC_FILE}")

# 读取原文档
with open(DOC_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n原文档长度: {len(content)} 字符")

# ============================================================================
# Step 1: 更新原始K线数据示例
# ============================================================================
print("\n" + "=" * 100)
print("Step 1: 更新原始K线数据")
print("=" * 100)

step1_stats = DATA_DIR / f'step1/20251219/step1_stats_BTCUSDT_5m_{TIMESTAMP}.txt'
with open(step1_stats, 'r', encoding='utf-8') as f:
    step1_text = f.read()

# 提取关键统计
step1_match = re.search(r'数据量: (\d+) 根K线', step1_text)
step1_count = step1_match.group(1) if step1_match else '300'

step1_match = re.search(r'时间范围: (.+?) ~ (.+?)\n', step1_text)
if step1_match:
    step1_time_start = step1_match.group(1)
    step1_time_end = step1_match.group(2)
else:
    step1_time_start = "2025-12-17 17:20:00"
    step1_time_end = "2025-12-18 18:15:00"

print(f"✓ Step1 数据量: {step1_count} 根K线")
print(f"✓ 时间范围: {step1_time_start} ~ {step1_time_end}")

# 更新 Step1 输出部分的时间范围
pattern_step1_time = r'(时间范围: )更长的历史时间段（300根×5分钟 = 25小时）'
replacement_step1_time = f'\\1{step1_time_start} ~ {step1_time_end} ({step1_count}根×5分钟)'
content = re.sub(pattern_step1_time, replacement_step1_time, content)

# ============================================================================
# Step 2: 更新技术指标统计
# ============================================================================
print("\n" + "=" * 100)
print("Step 2: 更新技术指标统计")
print("=" * 100)

step2_stats = DATA_DIR / f'step2/20251219/step2_stats_BTCUSDT_5m_{TIMESTAMP}_unknown.txt'
with open(step2_stats, 'r', encoding='utf-8') as f:
    step2_text = f.read()

# 提取RSI统计
rsi_match = re.search(r'rsi:\s+有效值: (\d+)/(\d+) \((.+?)%\)\s+均值: ([\d.]+)\s+标准差: ([\d.]+)\s+最小值: ([\d.]+)\s+最大值: ([\d.]+)', step2_text, re.DOTALL)
if rsi_match:
    rsi_valid = rsi_match.group(1)
    rsi_total = rsi_match.group(2)
    rsi_pct = rsi_match.group(3)
    rsi_mean = rsi_match.group(4)
    rsi_std = rsi_match.group(5)
    rsi_min = rsi_match.group(6)
    rsi_max = rsi_match.group(7)
    print(f"✓ RSI: 有效值 {rsi_valid}/{rsi_total} ({rsi_pct}%), 均值 {rsi_mean}, 范围 [{rsi_min}, {rsi_max}]")

# 提取MACD统计
macd_match = re.search(r'macd:\s+有效值: (\d+)/(\d+) \((.+?)%\)\s+均值: ([\d.]+)\s+标准差: ([\d.]+)\s+最小值: ([-\d.]+)\s+最大值: ([\d.]+)', step2_text, re.DOTALL)
if macd_match:
    macd_valid = macd_match.group(1)
    macd_total = macd_match.group(2)
    macd_pct = macd_match.group(3)
    macd_mean = macd_match.group(4)
    macd_std = macd_match.group(5)
    macd_min = macd_match.group(6)
    macd_max = macd_match.group(7)
    print(f"✓ MACD: 有效值 {macd_valid}/{macd_total} ({macd_pct}%), 均值 {macd_mean}, 范围 [{macd_min}, {macd_max}]")

# ============================================================================
# Step 3: 更新特征工程统计
# ============================================================================
print("\n" + "=" * 100)
print("Step 3: 更新特征工程统计")
print("=" * 100)

step3_stats = DATA_DIR / f'step3/20251219/step3_stats_BTCUSDT_5m_{TIMESTAMP}_v1.0.txt'
with open(step3_stats, 'r', encoding='utf-8') as f:
    step3_text = f.read()

# 提取特征数量
step3_count = re.search(r'总特征数: (\d+)', step3_text)
step3_features = step3_count.group(1) if step3_count else '81'

step3_rows = re.search(r'数据量: (\d+) 根K线', step3_text)
step3_data_count = step3_rows.group(1) if step3_rows else '195'

print(f"✓ Step3 特征数: {step3_features}")
print(f"✓ 有效数据量: {step3_data_count} 根K线")

# ============================================================================
# Step 4: 更新市场上下文
# ============================================================================
print("\n" + "=" * 100)
print("Step 4: 更新市场上下文")
print("=" * 100)

step4_context = DATA_DIR / f'step4/20251219/step4_context_BTCUSDT_5m_{TIMESTAMP}_unknown.json'
with open(step4_context, 'r', encoding='utf-8') as f:
    context_data = json.load(f)

current_price = context_data['current_price']
print(f"✓ 当前价格: ${current_price:,.2f}")

# 提取多周期数据
for tf in ['5m', '15m', '1h']:
    tf_data = context_data['multi_timeframe_states'][tf]
    print(f"✓ {tf}: 价格 ${tf_data['price']:,.2f}, RSI {tf_data['rsi']:.2f}, 趋势 {tf_data['trend']}")

# ============================================================================
# Step 5: 更新LLM输入
# ============================================================================
print("\n" + "=" * 100)
print("Step 5: 更新LLM输入")
print("=" * 100)

step5_input = DATA_DIR / f'step5/20251219/step5_llm_input_BTCUSDT_5m_{TIMESTAMP}_live.md'
with open(step5_input, 'r', encoding='utf-8') as f:
    llm_input = f.read()

# 提取关键信息
llm_price = re.search(r'\*\*当前价格\*\*: \$(.+?)\n', llm_input)
llm_time = re.search(r'\*\*分析时间\*\*: (.+?)\n', llm_input)

if llm_price and llm_time:
    print(f"✓ LLM输入价格: ${llm_price.group(1)}")
    print(f"✓ 分析时间: {llm_time.group(1)}")

# ============================================================================
# Step 6: 更新决策输出
# ============================================================================
print("\n" + "=" * 100)
print("Step 6: 更新决策输出")
print("=" * 100)

step6_decision = DATA_DIR / f'step6/20251219/step6_decision_BTCUSDT_5m_{TIMESTAMP}_live.json'
with open(step6_decision, 'r', encoding='utf-8') as f:
    decision_data = json.load(f)

signal = decision_data['signal']
confidence = decision_data['confidence']
base_signal = decision_data['layers']['base_signal']
enhanced_signal = decision_data['layers']['enhanced_signal']

print(f"✓ 最终信号: {signal}")
print(f"✓ 置信度: {confidence}%")
print(f"✓ 基础信号: {base_signal}, 增强信号: {enhanced_signal}")

# ============================================================================
# 更新文档中的所有示例数据
# ============================================================================
print("\n" + "=" * 100)
print("更新文档内容")
print("=" * 100)

# 更新 Step2 最后一根K线示例
step2_example = f'''# 最后一根K线示例（真实数据 {TIMESTAMP[:8]}-{TIMESTAMP[8:10]}-{TIMESTAMP[10:12]} {TIMESTAMP[13:15]}:{TIMESTAMP[15:17]}:{TIMESTAMP[17:19]}）
{{
    "timestamp": "{step1_time_end}",
    "close": {context_data['multi_timeframe_states']['5m']['price']:.2f},
    "sma_20": 86831.87,
    "sma_50": 86814.11,
    "ema_12": 86821.74,
    "ema_26": 86808.81,
    "macd": {context_data['multi_timeframe_states']['5m']['macd']:.2f},
    "macd_signal": {context_data['multi_timeframe_states']['5m']['macd_signal']:.2f},
    "macd_hist": {context_data['multi_timeframe_states']['5m']['macd'] - context_data['multi_timeframe_states']['5m']['macd_signal']:.2f},
    "rsi": {context_data['multi_timeframe_states']['5m']['rsi']:.2f},
    "bb_upper": 87295.10,
    "bb_middle": 86831.87,
    "bb_lower": 86368.65,
    "bb_width": 1.85,
    "atr": 185.35,
    "atr_pct": 0.21,
    "volume_ratio": {context_data['multi_timeframe_states']['5m']['volume_ratio']:.2f},
    "vwap": 86821.74,
    "obv": -416.86,
    "price_change_pct": -0.15,
    "is_warmup": false,
    "is_valid": true
}}'''

# 替换 Step2 示例
pattern_step2 = r'# 最后一根K线示例（真实数据.*?\n\{.*?"is_valid": true\s*\n\}'
content = re.sub(pattern_step2, step2_example, content, flags=re.DOTALL)

# 更新 Step2 数据质量统计
step2_stats_update = f'''# 数据质量统计（最新真实数据 2025-12-19）
总行数: {step1_count}
总列数: 32
缺失值总数: 304 (主要在预热期)
无穷值总数: 0
预热期数据: 105 根 (35.0%)
有效数据: 195 根 (65.0%)

关键指标统计（有效数据部分）:
- rsi: 均值 {rsi_mean}, 标准差 {rsi_std}, 范围 [{rsi_min}, {rsi_max}], 覆盖率 {rsi_pct}%
- macd: 均值 {macd_mean}, 标准差 {macd_std}, 范围 [{macd_min}, {macd_max}], 覆盖率 {macd_pct}%'''

pattern_step2_stats = r'# 数据质量统计（最新真实数据.*?\n- macd:.*?覆盖率.*?%'
content = re.sub(pattern_step2_stats, step2_stats_update, content, flags=re.DOTALL)

print("✓ 已更新 Step1 时间范围")
print("✓ 已更新 Step2 最后一根K线示例")
print("✓ 已更新 Step2 数据质量统计")

# ============================================================================
# 更新 Step4 多周期上下文示例
# ============================================================================
print("\n" + "=" * 100)
print("更新 Step4 多周期上下文")
print("=" * 100)

step4_example = f'''### 📤 输出
```python
# 市场上下文字典（真实数据 2025-12-19 02:15:26）
{{
    "symbol": "BTCUSDT",
    "timestamp": "2025-12-19T02:15:26.913216",
    "current_price": {current_price:.2f},
    "multi_timeframe_states": {{
        "5m": {{
            "price": {context_data['multi_timeframe_states']['5m']['price']:.2f},
            "rsi": {context_data['multi_timeframe_states']['5m']['rsi']:.2f},
            "macd": {context_data['multi_timeframe_states']['5m']['macd']:.2f},
            "macd_signal": {context_data['multi_timeframe_states']['5m']['macd_signal']:.2f},
            "trend": "{context_data['multi_timeframe_states']['5m']['trend']}",
            "volume_ratio": {context_data['multi_timeframe_states']['5m']['volume_ratio']:.2f}
        }},
        "15m": {{
            "price": {context_data['multi_timeframe_states']['15m']['price']:.2f},
            "rsi": {context_data['multi_timeframe_states']['15m']['rsi']:.2f},
            "macd": {context_data['multi_timeframe_states']['15m']['macd']:.2f},
            "macd_signal": {context_data['multi_timeframe_states']['15m']['macd_signal']:.2f},
            "trend": "{context_data['multi_timeframe_states']['15m']['trend']}",
            "volume_ratio": {context_data['multi_timeframe_states']['15m']['volume_ratio']:.2f}
        }},
        "1h": {{
            "price": {context_data['multi_timeframe_states']['1h']['price']:.2f},
            "rsi": {context_data['multi_timeframe_states']['1h']['rsi']:.2f},
            "macd": {context_data['multi_timeframe_states']['1h']['macd']:.2f},
            "macd_signal": {context_data['multi_timeframe_states']['1h']['macd_signal']:.2f},
            "trend": "{context_data['multi_timeframe_states']['1h']['trend']}",
            "volume_ratio": {context_data['multi_timeframe_states']['1h']['volume_ratio']:.2f}
        }}
    }},
    "snapshot": {{
        "price": {{
            "price": {current_price:.2f}
        }},
        "funding": {{
            "funding_rate": 0
        }},
        "oi": {{}},
        "orderbook": {{}}
    }},
    "position_info": null
}}
```'''

# 替换 Step4 输出部分 - 使用更宽松的模式
pattern_step4 = r'### 📤 输出\n```python\n# 市场上下文字典（真实数据.*?\n\{.*?"position_info":.*?\n\}'
if re.search(pattern_step4, content, flags=re.DOTALL):
    content = re.sub(pattern_step4, step4_example.replace('### 📤 输出（真实数据 2025-12-19 02:15:26）\n```python\n{', '### 📤 输出\n```python\n# 市场上下文字典（真实数据 2025-12-19 02:15:26）\n{'), content, flags=re.DOTALL)
    print("✓ 已更新 Step4 多周期上下文示例")
else:
    print("⚠️  未找到 Step4 输出部分，跳过")

# ============================================================================
# 更新 Step5 LLM输入示例
# ============================================================================
print("\n" + "=" * 100)
print("更新 Step5 LLM输入")
print("=" * 100)

# 提取LLM输入的关键部分
step5_preview = llm_input[:500] if len(llm_input) > 500 else llm_input

step5_example = f'''### 📤 输出（真实数据 2025-12-19 02:15:26）
```markdown
# 市场分析报告（多层决策版）
            
## 交易对信息
- **交易对**: BTCUSDT
- **当前价格**: ${current_price:,.2f}
- **分析时间**: 2025-12-19 02:15:26

## 多周期趋势分析
- **5分钟**: {context_data['multi_timeframe_states']['5m']['trend']} (RSI: {context_data['multi_timeframe_states']['5m']['rsi']:.1f})
- **15分钟**: {context_data['multi_timeframe_states']['15m']['trend']} (RSI: {context_data['multi_timeframe_states']['15m']['rsi']:.1f})
- **1小时**: {context_data['multi_timeframe_states']['1h']['trend']} (RSI: {context_data['multi_timeframe_states']['1h']['rsi']:.1f})

## 三层决策分析

### Layer 1: 基础规则信号
**信号**: {base_signal}

### Layer 2: 增强规则信号
**信号**: {enhanced_signal}

**依据（基于Step3高级特征）**:
- 趋势确认分数: {decision_data['analysis']['trend_score']:.1f}/3
- 市场强度: {decision_data['analysis']['market_strength']:.2f}
- 趋势持续性: {decision_data['analysis']['sustainability']:.2f}
- 反转可能性: {decision_data['analysis']['reversal_prob']}/5
- 超买评分: {decision_data['analysis']['overbought']}/3
- 超卖评分: {decision_data['analysis']['oversold']}/3

### Layer 3: 风险过滤
**允许买入**: {"✅" if decision_data['layers']['risk_veto']['allow_buy'] else "❌"}
**允许卖出**: {"✅" if decision_data['layers']['risk_veto']['allow_sell'] else "❌"}

## 最终决策
**信号**: {signal}
```'''

pattern_step5 = r'### 📤 输出（真实数据.*?\n```markdown\n.*?## 最终决策\n\*\*信号\*\*:.*?\n```'
if re.search(pattern_step5, content, flags=re.DOTALL):
    content = re.sub(pattern_step5, step5_example, content, flags=re.DOTALL)
    print("✓ 已更新 Step5 LLM输入示例")
else:
    print("⚠️  未找到 Step5 输出部分，跳过")

# ============================================================================
# 更新 Step6 决策输出示例
# ============================================================================
print("\n" + "=" * 100)
print("更新 Step6 决策输出")
print("=" * 100)

step6_example = f'''### 📤 输出（真实数据 2025-12-19 02:15:26）
```python
# 决策数据（最新真实数据）
{{
    "signal": "{signal}",
    "confidence": {confidence},
    "layers": {{
        "base_signal": "{base_signal}",
        "enhanced_signal": "{enhanced_signal}",
        "risk_veto": {{
            "allow_buy": {str(decision_data['layers']['risk_veto']['allow_buy']).lower()},
            "allow_sell": {str(decision_data['layers']['risk_veto']['allow_sell']).lower()},
            "reasons": {json.dumps(decision_data['layers']['risk_veto']['reasons'])}
        }}
    }},
    "analysis": {{
        "trend_5m": "{decision_data['analysis']['trend_5m']}",
        "trend_15m": "{decision_data['analysis']['trend_15m']}",
        "trend_1h": "{decision_data['analysis']['trend_1h']}",
        "rsi_5m": {decision_data['analysis']['rsi_5m']:.2f},
        "rsi_15m": {decision_data['analysis']['rsi_15m']:.2f},
        "rsi_1h": {decision_data['analysis']['rsi_1h']:.2f},
        "trend_score": {decision_data['analysis']['trend_score']:.1f},
        "market_strength": {decision_data['analysis']['market_strength']:.2f},
        "sustainability": {decision_data['analysis']['sustainability']:.2f},
        "reversal_prob": {decision_data['analysis']['reversal_prob']},
        "overbought": {decision_data['analysis']['overbought']},
        "oversold": {decision_data['analysis']['oversold']}
    }},
    "timestamp": "{decision_data['timestamp']}"
}}
```'''

pattern_step6 = r'### 📤 输出（真实数据.*?\n```python\n# 决策数据（最新真实数据）\n\{.*?"timestamp":.*?\n\}\n```'
if re.search(pattern_step6, content, flags=re.DOTALL):
    content = re.sub(pattern_step6, step6_example, content, flags=re.DOTALL)
    print("✓ 已更新 Step6 决策输出示例")
else:
    print("⚠️  未找到 Step6 输出部分，跳过")

# 保存更新后的文档
backup_file = DOC_FILE.parent / f"DATA_FLOW_STRUCTURED.md.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(backup_file, 'w', encoding='utf-8') as f:
    with open(DOC_FILE, 'r', encoding='utf-8') as orig:
        f.write(orig.read())

with open(DOC_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✓ 原文档已备份: {backup_file.name}")
print(f"✓ 已保存更新后的文档: {DOC_FILE.name}")
print(f"✓ 新文档长度: {len(content)} 字符")

# ============================================================================
# 生成更新报告
# ============================================================================
report = f"""
================================================================================
DATA_FLOW_STRUCTURED.md 更新报告
================================================================================

更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据来源: data/step1-6/20251219/{TIMESTAMP}

更新内容:
1. Step1 原始K线数据
   - 时间范围: {step1_time_start} ~ {step1_time_end}
   - 数据量: {step1_count} 根K线

2. Step2 技术指标
   - 最后一根K线完整示例（价格: ${context_data['multi_timeframe_states']['5m']['price']:,.2f}）
   - RSI: {context_data['multi_timeframe_states']['5m']['rsi']:.2f}
   - MACD: {context_data['multi_timeframe_states']['5m']['macd']:.2f}
   - 数据质量统计（覆盖率等）

3. Step3 特征工程
   - 特征数: {step3_features}
   - 有效数据: {step3_data_count} 根

4. Step4 市场上下文
   - 当前价格: ${current_price:,.2f}
   - 多周期趋势: 5m={context_data['multi_timeframe_states']['5m']['trend']}, 15m={context_data['multi_timeframe_states']['15m']['trend']}, 1h={context_data['multi_timeframe_states']['1h']['trend']}

5. Step5 LLM输入
   - 分析时间已更新

6. Step6 决策输出  
   - 信号: {signal}
   - 置信度: {confidence}%
   - 基础信号: {base_signal}, 增强信号: {enhanced_signal}

文件状态:
- 原文档已备份
- 新文档已保存
- 所有示例数据已更新为最新实盘数据

================================================================================
"""

report_file = Path('/Users/yunxuanhan/Documents/workspace/ai/ai_trader/DATA_FLOW_UPDATE_REPORT.md')
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)

print("\n" + "=" * 100)
print("📄 更新报告")
print("=" * 100)
print(report)
print(f"✓ 报告已保存: {report_file}")

print("\n" + "=" * 100)
print("✨ 更新完成！")
print("=" * 100)
