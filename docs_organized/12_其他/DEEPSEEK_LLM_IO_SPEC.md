# DeepSeek LLM 输入输出规格说明

## 📋 概述

本文档详细说明 DeepSeek LLM 在 AI 量化交易系统中的输入输出规格。

**当前状态**: ⚠️ **系统已实现 LLM 模块，但未在实盘中启用**  
**实盘使用**: 基于规则的决策逻辑（`run_live_trading.py: generate_signal()`）  
**LLM 模块**: 已完整实现（`src/strategy/deepseek_engine.py`），可随时切换

---

## 🔄 DeepSeek 在数据流中的位置

```
Step 4: 构建多周期上下文
   ↓ [市场上下文JSON]
   
Step 5: 格式化Markdown文本
   ↓ [LLM 友好的文本]
   
┌──────────────────────────────────────┐
│  DeepSeek LLM 决策引擎 (可选)         │
│  输入: Markdown 市场分析              │
│  输出: JSON 交易决策                  │
└──────────────────────────────────────┘
   ↓ [AI 生成的决策]
   
Step 6: 生成交易决策
   ↓ [BUY/SELL/HOLD]
   
Step 7: 执行交易
```

**注意**: 当前实盘系统在 Step 6 直接使用规则引擎，跳过了 LLM 调用。

---

## 📥 LLM 输入 (Input)

### 输入来源
- **Step 4**: 多周期市场上下文 (JSON)
- **Step 5**: 格式化的 Markdown 文本

### 输入结构

#### 1. System Prompt (系统提示词)
```
你是一个专业的加密货币合约交易 AI Agent。

## 核心目标
1. 保住本金优先 - 控制风险是第一要务
2. 最大化长期夏普比率 - 追求风险调整后收益
3. 严格遵守风险管理规则

## 决策原则
1. 不允许超出最大风险敞口 - 永远不要让单笔交易风险超过账户的1.5%
2. 不允许逆大周期趋势重仓 - 只在趋势明确时加大仓位
3. 资金费率极端时谨慎 - 极端资金费率说明市场过热
4. 流动性不足时避免交易 - 低流动性可能导致滑点
5. 持仓时关注止盈止损 - 及时锁定利润或止损

## 输出格式
你必须输出严格的JSON格式，包含action, confidence, reasoning等字段
```

**代码位置**: `src/strategy/deepseek_engine.py: _build_system_prompt()`

---

#### 2. User Prompt (用户输入 - 市场数据)

##### 格式化的 Markdown 文本
```markdown
# 市场分析报告
            
## 交易对信息
- **交易对**: BTCUSDT
- **当前价格**: $89,782.00
- **分析时间**: 2025-12-17 23:35:10

## 多周期趋势分析
- **5分钟**: uptrend (RSI: 71.6)
- **15分钟**: uptrend (RSI: 75.5)
- **1小时**: uptrend (RSI: 73.1)

## 趋势统计
- 上涨周期数: 3/3
- 下跌周期数: 0/3

## 技术指标详情 (5m 周期)
- **MACD**: 0.15
- **MACD Signal**: 0.13
- **MACD Histogram**: 0.02
- **布林带宽度**: 1.23%
- **ATR**: 0.17%
- **成交量比率**: 1.25

## 市场快照
- **最新价格**: $89,782.00
- **买一价**: $89,780.00
- **卖一价**: $89,784.00

## 持仓信息
- 当前无持仓

## 决策建议
请基于以上信息分析：
1. 多周期趋势是否一致
2. RSI 是否过热/过冷
3. MACD 是否支持趋势
4. 成交量是否确认趋势
5. 是否有高胜率的交易机会

请严格按照JSON格式输出你的决策。
```

**数据来源**:
- Step 4 的市场上下文
- Step 5 的格式化逻辑

**代码位置**: 
- `run_live_trading.py: 154-176` (格式化逻辑)
- `src/features/builder.py: format_for_llm()` (可选的格式化方法)

---

#### 3. 原始市场数据 (附加上下文)
```python
{
    "symbol": "BTCUSDT",
    "timestamp": "2025-12-17T23:35:10.134048",
    "current_price": 89782.0,
    "timeframes": {
        "5m": {
            "price": 89782.0,
            "rsi": 71.60,
            "macd": 0.15,
            "macd_signal": 0.13,
            "trend": "uptrend",
            "sma_20": 89650.5,
            "sma_50": 89500.2
        },
        "15m": {
            "price": 89780.0,
            "rsi": 75.48,
            "macd": 0.18,
            "macd_signal": 0.15,
            "trend": "uptrend"
        },
        "1h": {
            "price": 89785.0,
            "rsi": 73.11,
            "macd": 0.12,
            "macd_signal": 0.10,
            "trend": "uptrend"
        }
    },
    "snapshot": {
        "price": {
            "last": 89782.0,
            "bid": 89780.0,
            "ask": 89784.0
        },
        "funding": {},
        "oi": {},
        "orderbook": {}
    },
    "position_info": null,
    "account_balance": 139.31
}
```

---

### API 调用参数
```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.3,              # 低温度确保稳定输出
    max_tokens=2000,              # 最大输出长度
    response_format={"type": "json_object"}  # 强制JSON格式
)
```

**代码位置**: `src/strategy/deepseek_engine.py: make_decision()`

---

## 📤 LLM 输出 (Output)

### 标准输出格式 (JSON)

```json
{
  "action": "hold",
  "symbol": "BTCUSDT",
  "confidence": 35,
  "leverage": 1,
  "position_size_pct": 0.0,
  "stop_loss_pct": 1.0,
  "take_profit_pct": 2.0,
  "entry_price": 89782.0,
  "stop_loss_price": 88884.18,
  "take_profit_price": 91577.64,
  "risk_reward_ratio": 2.0,
  "reasoning": "虽然多周期趋势一致向上(5m/15m/1h均为uptrend)，但RSI已经过热(5m: 71.6, 15m: 75.5, 1h: 73.1)，15分钟周期RSI超过75阈值，存在短期回调风险。MACD虽然呈多头排列，但上涨动能减弱。建议观望，等待RSI回落至60以下再考虑入场。",
  "analysis": {
    "trend_analysis": "多周期趋势一致：5m上涨，15m上涨，1h上涨。短中长期趋势共振向上，SMA20>SMA50且价格在均线之上。",
    "technical_signals": "RSI过热(5m:71.6, 15m:75.5, 1h:73.1)，MACD金叉但柱状图缩小(0.02)，成交量比率1.25显示量能温和。",
    "risk_assessment": "RSI超买区间，回调风险较高。布林带宽度1.23%显示波动率正常。ATR 0.17%为低波动率环境。",
    "market_sentiment": "价格接近日内高位，短期追高风险较大。资金费率数据缺失，无法判断多空情绪。",
    "key_levels": "支撑位: 89650 (SMA20), 89100 (BB下轨)。阻力位: 90200 (BB上轨)。",
    "decision_rationale": "综合判断：虽然趋势向上，但RSI过热且处于超买区间，不适合追高开仓。等待回调至支撑位附近(89650-89500)再考虑做多机会。当前观望为最优策略。"
  },
  "metadata": {
    "analyzed_timeframes": ["5m", "15m", "1h"],
    "primary_indicators": ["RSI", "MACD", "SMA", "BB", "ATR", "Volume"],
    "market_condition": "uptrend_overbought",
    "risk_level": "medium"
  },
  "timestamp": "2025-12-17T23:35:10.134048",
  "model": "deepseek-chat",
  "raw_response": "{...}"  # 完整的 LLM 原始响应
}
```

---

### 字段说明

#### 核心决策字段
| 字段 | 类型 | 说明 | 可选值/范围 |
|------|------|------|------------|
| `action` | string | 交易动作 | `open_long`, `open_short`, `close_position`, `add_position`, `reduce_position`, `hold` |
| `symbol` | string | 交易对 | `BTCUSDT`, `ETHUSDT` 等 |
| `confidence` | int | 决策置信度 | 0-100，<50应选择hold |
| `leverage` | int | 建议杠杆 | 1-5，高波动率降低杠杆 |
| `position_size_pct` | float | 仓位占比 | 0-30%，风险敞口控制 |

#### 风控字段
| 字段 | 类型 | 说明 | 计算方式 |
|------|------|------|---------|
| `stop_loss_pct` | float | 止损百分比 | 默认1-3% |
| `take_profit_pct` | float | 止盈百分比 | 默认2-6% |
| `entry_price` | float | 建议入场价 | 当前价或限价 |
| `stop_loss_price` | float | 止损价位 | entry_price * (1 - stop_loss_pct/100) |
| `take_profit_price` | float | 止盈价位 | entry_price * (1 + take_profit_pct/100) |
| `risk_reward_ratio` | float | 风险收益比 | take_profit_pct / stop_loss_pct |

#### 分析字段 (analysis)
```json
{
  "trend_analysis": "多周期趋势分析",
  "technical_signals": "技术指标信号汇总",
  "risk_assessment": "风险评估",
  "market_sentiment": "市场情绪判断",
  "key_levels": "关键支撑阻力位",
  "decision_rationale": "决策依据"
}
```

#### 元数据字段 (metadata)
```json
{
  "analyzed_timeframes": ["5m", "15m", "1h"],
  "primary_indicators": ["RSI", "MACD", "SMA", "BB"],
  "market_condition": "uptrend_overbought",
  "risk_level": "medium"  // low/medium/high
}
```

---

### 动作类型详解

#### 1. `open_long` (开多仓)
```json
{
  "action": "open_long",
  "confidence": 75,
  "leverage": 3,
  "position_size_pct": 15.0,
  "stop_loss_pct": 1.5,
  "take_profit_pct": 3.0,
  "reasoning": "多周期趋势向上，RSI回调至支撑位，MACD金叉确认上涨动能"
}
```

#### 2. `open_short` (开空仓)
```json
{
  "action": "open_short",
  "confidence": 80,
  "leverage": 2,
  "position_size_pct": 12.0,
  "stop_loss_pct": 2.0,
  "take_profit_pct": 4.0,
  "reasoning": "多周期趋势向下，RSI超买回落，MACD死叉确认下跌动能"
}
```

#### 3. `hold` (观望)
```json
{
  "action": "hold",
  "confidence": 30,
  "leverage": 1,
  "position_size_pct": 0.0,
  "reasoning": "趋势不明确，RSI处于中性区间，等待更明确的信号"
}
```

#### 4. `close_position` (平仓)
```json
{
  "action": "close_position",
  "confidence": 85,
  "reasoning": "趋势反转信号出现，及时止盈/止损"
}
```

#### 5. `add_position` (加仓)
```json
{
  "action": "add_position",
  "confidence": 70,
  "position_size_pct": 5.0,
  "reasoning": "原有持仓方向正确，趋势延续，适度加仓"
}
```

#### 6. `reduce_position` (减仓)
```json
{
  "action": "reduce_position",
  "confidence": 60,
  "position_size_pct": 5.0,
  "reasoning": "部分止盈，降低风险敞口"
}
```

---

## 🔧 代码集成点

### 1. LLM 引擎初始化
```python
# src/strategy/deepseek_engine.py
from openai import OpenAI

class StrategyEngine:
    def __init__(self):
        self.api_key = config.deepseek.get('api_key')
        self.base_url = 'https://api.deepseek.com'
        self.model = 'deepseek-chat'
        self.temperature = 0.3
        self.max_tokens = 2000
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
```

---

### 2. 调用 LLM 生成决策
```python
# src/strategy/deepseek_engine.py
def make_decision(self, market_context_text: str, market_context_data: Dict) -> Dict:
    """
    调用 DeepSeek LLM 生成交易决策
    
    Args:
        market_context_text: Step5 生成的 Markdown 文本
        market_context_data: Step4 生成的市场上下文
    
    Returns:
        JSON 格式的决策结果
    """
    system_prompt = self._build_system_prompt()
    user_prompt = self._build_user_prompt(market_context_text)
    
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=self.temperature,
        max_tokens=self.max_tokens,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    decision = json.loads(content)
    
    return decision
```

---

### 3. 在实盘交易中启用 LLM（可选）

**当前实现** (基于规则):
```python
# run_live_trading.py: generate_signal()
def generate_signal(self, market_state: Dict) -> str:
    # 规则引擎
    if uptrend_count >= 2 and rsi_1h < 70 and rsi_15m < 75:
        return 'BUY'
    elif downtrend_count >= 2 or (rsi_5m > 80 and rsi_15m > 75):
        return 'SELL'
    else:
        return 'HOLD'
```

**启用 LLM** (需修改):
```python
# run_live_trading.py (修改版)
from src.strategy.deepseek_engine import StrategyEngine

class LiveTradingBot:
    def __init__(self, config: Dict = None):
        # ...existing code...
        self.strategy_engine = StrategyEngine()  # 初始化 LLM
    
    def run_once(self):
        # ...existing code...
        
        # Step 5: 格式化 Markdown
        markdown_text = self._format_markdown(market_state)
        
        # 🆕 调用 LLM 生成决策
        llm_decision = self.strategy_engine.make_decision(
            market_context_text=markdown_text,
            market_context_data=market_state
        )
        
        # 提取信号
        signal = self._map_action_to_signal(llm_decision['action'])
        
        # Step 6: 保存决策
        self.data_saver.save_step6_decision(llm_decision, symbol, '5m', 'live')
        
        # Step 7: 执行交易
        if signal != 'HOLD':
            self.execute_trade(signal, market_state, llm_decision)
```

---

## 🔄 数据流转示例

### 完整流程（启用 LLM）

```
Step 4 输出:
{
  "symbol": "BTCUSDT",
  "current_price": 89782.0,
  "timeframes": {
    "5m": {"trend": "uptrend", "rsi": 71.6},
    "15m": {"trend": "uptrend", "rsi": 75.5},
    "1h": {"trend": "uptrend", "rsi": 73.1}
  }
}
        ↓
        
Step 5 输出:
"""
# 市场分析报告
- 5分钟: uptrend (RSI: 71.6)
- 15分钟: uptrend (RSI: 75.5)
- 1小时: uptrend (RSI: 73.1)
"""
        ↓
        
DeepSeek LLM 输入:
{
  "messages": [
    {"role": "system", "content": "你是专业的交易AI..."},
    {"role": "user", "content": "# 市场分析报告\n..."}
  ],
  "temperature": 0.3,
  "response_format": {"type": "json_object"}
}
        ↓
        
DeepSeek LLM 输出:
{
  "action": "hold",
  "confidence": 35,
  "reasoning": "RSI过热，建议观望...",
  "analysis": {...}
}
        ↓
        
Step 6 保存决策:
data/step6/20251217/step6_decision_BTCUSDT_5m_20251217_233510_live.json
        ↓
        
Step 7 执行交易:
signal = "HOLD" → 不执行交易
```

---

## 📊 输入输出对比表

| 项目 | 输入 (Input) | 输出 (Output) |
|------|-------------|--------------|
| **数据来源** | Step 4 + Step 5 | LLM 生成的 JSON |
| **格式** | Markdown 文本 + JSON 上下文 | 标准 JSON |
| **数据量** | ~500-2000 字符 | ~1000-3000 字符 |
| **包含信息** | 价格、趋势、指标、统计 | 动作、置信度、分析、推理 |
| **更新频率** | 每次运行 (5分钟) | 每次 LLM 调用 |
| **保存位置** | step4/, step5/ | step6/ |

---

## ⚠️ 注意事项

### 1. API 成本
- DeepSeek API 按 token 计费
- 建议设置调用频率限制（如每5分钟）
- 监控 API 使用量和成本

### 2. 延迟风险
- LLM 调用可能需要 2-10 秒
- 高频交易场景不适合实时调用
- 建议使用缓存或异步处理

### 3. 输出验证
- 必须验证 JSON 格式正确性
- 检查必填字段是否存在
- 验证数值范围是否合理

### 4. 错误处理
```python
try:
    decision = llm.make_decision(...)
except Exception as e:
    # 回退到规则引擎
    decision = rule_based_decision(...)
```

### 5. 安全性
- 不要在提示词中泄露敏感信息
- API Key 存储在环境变量中
- 定期轮换 API Key

---

## 🚀 启用 LLM 的步骤

### 1. 配置 API Key
```bash
# .env
DEEPSEEK_API_KEY=your_api_key_here
```

### 2. 修改代码
在 `run_live_trading.py` 中集成 `StrategyEngine`

### 3. 测试
```bash
# 测试 LLM 调用
python test_deepseek_engine.py

# 小仓位实盘测试
python run_live_trading.py --test-mode
```

### 4. 监控
- 记录每次 LLM 调用的延迟
- 统计决策准确率
- 监控 API 成本

---

## 📚 相关文档

- [数据流转结构化文档](DATA_FLOW_STRUCTURED.md)
- [DeepSeek 引擎源码](src/strategy/deepseek_engine.py)
- [实盘交易脚本](run_live_trading.py)
- [配置文件](src/config.py)

---

📅 最后更新: 2025-12-18  
✍️ 作者: AI Trader Team  
🔄 版本: v1.0 (LLM IO 规格)
