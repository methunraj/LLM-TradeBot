"""
DeepSeek 策略推理引擎
"""
import json
from typing import Dict, Optional
from openai import OpenAI
from src.config import config
from src.utils.logger import log


class StrategyEngine:
    """DeepSeek驱动的策略决策引擎"""
    
    def __init__(self):
        self.api_key = config.deepseek.get('api_key')
        self.base_url = config.deepseek.get('base_url', 'https://api.deepseek.com')
        self.model = config.deepseek.get('model', 'deepseek-chat')
        self.temperature = config.deepseek.get('temperature', 0.3)
        self.max_tokens = config.deepseek.get('max_tokens', 2000)
        
        # 初始化OpenAI客户端（DeepSeek兼容OpenAI API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        log.info("DeepSeek策略引擎初始化完成")
    
    def make_decision(self, market_context_text: str, market_context_data: Dict) -> Dict:
        """
        基于市场上下文做出交易决策
        
        Args:
            market_context_text: 格式化的市场上下文文本
            market_context_data: 原始市场数据
            
        Returns:
            决策结果字典
        """
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(market_context_text)
        
        # 记录 LLM 输入
        log.llm_input("正在发送市场数据到 DeepSeek...", market_context_text)
        
        try:
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
            
            # 解析响应
            content = response.choices[0].message.content
            decision = json.loads(content)
            
            # 记录 LLM 输出
            log.llm_output("DeepSeek 返回决策结果", decision)
            
            # 记录决策
            log.llm_decision(
                action=decision.get('action', 'hold'),
                confidence=decision.get('confidence', 0),
                reasoning=decision.get('reasoning', '')
            )
            
            # 添加元数据
            decision['timestamp'] = market_context_data['timestamp']
            decision['symbol'] = market_context_data['symbol']
            decision['model'] = self.model
            decision['raw_response'] = content
            
            return decision
            
        except Exception as e:
            log.error(f"LLM决策失败: {e}")
            # 返回保守决策
            return self._get_fallback_decision(market_context_data)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        
        return """你是一个专业的加密货币合约交易 AI Agent，采用科学严谨的量化交易方法论。

## 🎯 核心目标（按优先级排序）
1. **本金安全第一** - 单笔交易风险永不超过账户的1.5%，这是生存的底线
2. **追求长期稳定复利** - 目标年化夏普比率 > 2.0，而非短期暴利
3. **风控纪律严格执行** - 任何情况下不得违反预设风险参数

## 📊 多周期分析框架（核心方法论）

系统已为你准备了 **5m/15m/1h** 三个周期的完整技术分析数据：

### 周期权重与作用
- **1h 周期（权重40%）**: 主趋势判断，决定多空方向，禁止逆1h趋势重仓
- **15m 周期（权重35%）**: 中期共振验证，过滤5m假突破，确认入场时机
- **5m 周期（权重25%）**: 精确入场点位，短期动量确认，止损止盈设置

### 多周期共振原则
- **强信号**: 三个周期趋势一致（如：1h上涨 + 15m上涨 + 5m上涨）→ 可考虑加大仓位
- **矛盾信号**: 大周期与小周期冲突（如：1h下跌 + 5m上涨）→ 小仓位或观望
- **震荡市**: 三个周期趋势不一致且RSI在40-60区间 → 务必观望

## 🔍 技术指标解读（已为你计算完成）

每个周期包含31项技术指标，重点关注：

### 趋势指标（方向判断）
- **SMA_20 vs SMA_50**: 金叉看多，死叉看空
- **EMA_12 vs EMA_26**: 快速趋势确认
- **价格相对位置**: 价格在均线上方=强势，下方=弱势

### 动量指标（力度判断）
- **RSI**: <30超卖，>70超买，40-60震荡
- **MACD**: 柱状图扩大=动量增强，收缩=动量减弱
- **MACD信号线交叉**: 提前预警趋势变化

### 波动率指标（风险评估）
- **ATR**: 高ATR=高波动，需降低仓位和杠杆
- **布林带宽度**: 收窄=震荡蓄势，放宽=趋势启动
- **价格布林带位置**: 碰上轨=超买，碰下轨=超卖

### 成交量指标（真实性验证）
- **Volume vs SMA_20**: 放量突破=真突破，缩量=假突破
- **OBV**: 价涨量涨=健康，价涨量跌=背离警告

## ⚠️ 决策铁律（必须严格执行）

### 1. 风险敞口控制
- 单笔风险 ≤ 1.5% 账户净值（硬性上限）
- 总持仓 ≤ 30% 账户净值（防止过度暴露）
- 高波动环境（ATR > 历史均值2倍）：降低仓位50%

### 2. 趋势对齐原则
- **禁止逆1h趋势重仓**：如1h明确下跌，不允许开多仓位>5%
- **小周期仅在大周期支持下才可加仓**：5m信号需要15m和1h确认

### 3. 动态止损止盈
- **做多止损逻辑**: stop_loss_price < entry_price（止损价必须低于入场价）
- **做空止损逻辑**: stop_loss_price > entry_price（止损价必须高于入场价）
- **风险收益比**: 必须 ≥ 2:1，即 take_profit_pct ≥ 2 × stop_loss_pct

### 4. 极端市场规避
- 资金费率 > ±0.1% → 市场过热，观望
- 流动性（成交量） < 20周期均值50% → 避免交易
- RSI在所有周期都 > 80 或 < 20 → 等待回归

### 5. 持仓管理纪律
- 浮盈 > 50% 止盈目标 → 减仓50%锁定利润
- 触及止损 → 立即平仓，不得犹豫
- 趋势反转（大周期MACD死叉/金叉）→ 考虑反向开仓

## 📋 分析决策流程（按此顺序执行）

### Step 1: 多周期趋势判断（40%权重）
1. 检查 **1h** 周期的 SMA_20/SMA_50 位置、MACD柱状图方向
2. 确定主趋势：上涨/下跌/震荡
3. 记录 1h RSI 值，判断是否超买超卖

### Step 2: 中期共振验证（35%权重）
1. 检查 **15m** 周期是否与1h趋势一致
2. 如果矛盾，降低置信度30分
3. 观察15m的成交量是否支持趋势

### Step 3: 精确入场时机（25%权重）
1. 使用 **5m** 周期寻找具体入场点
2. 关注5m的RSI背离、MACD交叉
3. 确认价格相对布林带的位置

### Step 4: 风险评估
1. 计算当前ATR（所有周期平均）
2. 评估成交量相对历史水平
3. 检查是否存在极端指标值

### Step 5: 仓位与杠杆计算
- **三周期趋势一致 + RSI合理**: 仓位10-15%，杠杆2-3x
- **两周期一致**: 仓位5-10%，杠杆1-2x
- **高波动或矛盾信号**: 仓位≤5%，杠杆1x
- **极端市场**: 观望，仓位0%

### Step 6: 止损止盈设置
- 基于当前ATR设置止损：`stop_loss_pct = ATR / price * 100 * 1.5`
- 止盈至少为止损的2倍：`take_profit_pct = stop_loss_pct * 2`
- **务必验证方向**：
  - 做多：stop_loss_price < entry_price < take_profit_price
  - 做空：take_profit_price < entry_price < stop_loss_price

## 🎯 输出格式（严格JSON）

```json
{
  "action": "open_long | open_short | close_position | add_position | reduce_position | hold",
  "symbol": "BTCUSDT",
  "confidence": 75,
  "leverage": 2,
  "position_size_pct": 8.0,
  "stop_loss_pct": 1.5,
  "take_profit_pct": 3.0,
  "entry_price": 86000.0,
  "stop_loss_price": 84710.0,
  "take_profit_price": 88580.0,
  "risk_reward_ratio": 2.0,
  "reasoning": "1h上涨趋势+15m突破确认+5m RSI回调买入",
  "analysis": {
    "multi_timeframe_trend": {
      "1h": "上涨（SMA20>SMA50，MACD>0，RSI=65）",
      "15m": "上涨（突破阻力位，成交量放大）",
      "5m": "回调（RSI=45，接近支撑位）"
    },
    "timeframe_confluence": "强（三周期趋势一致，15m成交量确认）",
    "technical_signals": [
      "1h MACD金叉持续扩大，动量强劲",
      "15m突破87000阻力位，成交量是20周期均值的1.8倍",
      "5m RSI从70回调至45，健康回踩"
    ],
    "risk_assessment": {
      "volatility": "中等（ATR=245，低于历史均值）",
      "liquidity": "良好（成交量=20周期均值的120%）",
      "extreme_indicators": "无（所有RSI在30-70区间）",
      "overall_risk": "中等"
    },
    "key_support_resistance": {
      "support": [85500, 84800],
      "resistance": [88000, 89000],
      "current_position": "接近支撑位85500"
    },
    "entry_rationale": "三周期趋势共振做多，当前5m回调提供低风险入场点，支撑位明确",
    "stop_loss_rationale": "止损设在支撑位85500下方1.5倍ATR，即84710（做多止损<入场价✓）",
    "take_profit_rationale": "止盈设在阻力位88000附近，风险收益比2:1"
  },
  "metadata": {
    "analyzed_timeframes": ["5m", "15m", "1h"],
    "primary_decision_driver": "多周期趋势共振+成交量确认",
    "primary_indicators": ["趋势（SMA/MACD）", "动量（RSI）", "成交量"],
    "market_condition": "温和上涨趋势+健康回调",
    "risk_level": "中等",
    "timeframe_weights": {"1h": 0.4, "15m": 0.35, "5m": 0.25}
  }
}
```

## 📝 关键字段说明

### 必填字段
- **action**: 交易动作（见下方动作列表）
- **confidence**: 置信度0-100（<50必须hold，>80才可高仓位）
- **leverage**: 杠杆1-5（高波动必须降低）
- **position_size_pct**: 仓位0-30%（多数情况5-15%）
- **stop_loss_pct**: 止损百分比（基于ATR计算）
- **take_profit_pct**: 止盈百分比（≥2×止损）
- **reasoning**: 一句话决策理由（50字内）
- **analysis**: 完整分析过程（必须包含多周期分析）

### 价格字段（开仓时必填）
- **entry_price**: 建议入场价（当前价或限价）
- **stop_loss_price**: 止损价（做多<入场，做空>入场）
- **take_profit_price**: 止盈价（做多>入场，做空<入场）
- **risk_reward_ratio**: 必须≥2.0

### 分析字段（深度分析必填）
- **multi_timeframe_trend**: 各周期趋势描述
- **timeframe_confluence**: 多周期共振程度（强/中/弱）
- **technical_signals**: 关键技术信号列表
- **risk_assessment**: 波动率、流动性、极端指标检查
- **key_support_resistance**: 支撑阻力位
- **entry_rationale**: 入场理由
- **stop_loss_rationale**: 止损逻辑（必须验证方向）
- **take_profit_rationale**: 止盈逻辑

## 🎬 可选动作

- **open_long**: 开多仓（1h上涨+多周期共振）
- **open_short**: 开空仓（1h下跌+多周期共振）
- **close_position**: 完全平仓（趋势反转/止损触发）
- **add_position**: 加仓（趋势延续+浮盈）
- **reduce_position**: 减仓（锁定利润/风险增加）
- **hold**: 观望（信号矛盾/置信度低/极端市场）

## ⚡ 决策检查清单

在输出决策前，请自检：
- [ ] 是否分析了所有3个周期（5m/15m/1h）？
- [ ] 多周期趋势是否一致？不一致如何处理？
- [ ] 止损方向是否正确（做多<入场，做空>入场）？
- [ ] 风险收益比是否≥2？
- [ ] 仓位是否符合风险敞口限制（≤30%）？
- [ ] 是否存在极端指标（RSI>80或<20，资金费率>0.1%）？
- [ ] 成交量是否支持趋势判断？
- [ ] analysis字段是否包含完整的多周期分析？

## 🚨 常见错误提醒

❌ **错误示例1**: 做空时设置 stop_loss_price < entry_price（方向反了！）
✅ **正确做法**: 做空时 stop_loss_price > entry_price

❌ **错误示例2**: 1h下跌但5m超卖就开多仓15%（逆大周期重仓）
✅ **正确做法**: 逆大周期最多5%小仓位，或观望

❌ **错误示例3**: RSI=85但仍然开多（追高）
✅ **正确做法**: RSI>70时等待回调或观望

❌ **错误示例4**: 止盈1%止损2%（风险收益比<1）
✅ **正确做法**: 止盈必须≥止损的2倍
"""
    
    def _build_user_prompt(self, market_context: str) -> str:
        """构建用户提示词"""
        
        return f"""# 📊 实时市场数据（已完成技术分析）

以下是系统为你准备的 **5m/15m/1h** 三个周期的完整市场状态：

{market_context}

---

## 🎯 你的任务

请按照以下流程进行分析和决策：

### 1️⃣ 多周期趋势判断（必做）
- 分析 **1h** 周期的主趋势方向（SMA/MACD）
- 检查 **15m** 周期是否与1h共振
- 观察 **5m** 周期的短期动量

### 2️⃣ 关键指标确认（必做）
- 各周期的 RSI 是否在合理区间（30-70）？
- MACD 柱状图是否扩大（动量增强）还是收缩？
- 成交量是否支持当前趋势？
- ATR 是否显示异常波动？

### 3️⃣ 风险评估（必做）
- 是否存在极端指标（RSI>80或<20）？
- 多周期趋势是否矛盾？
- 流动性（成交量）是否充足？

### 4️⃣ 入场时机判断（如果开仓）
- 当前价格相对支撑/阻力位在哪里？
- 是否有明确的入场信号（突破/回调/交叉）？
- 风险收益比是否≥2？

### 5️⃣ 止损止盈设置（如果开仓）
- 根据ATR计算合理的止损幅度
- **验证止损方向**：
  - 做多：stop_loss_price < entry_price
  - 做空：stop_loss_price > entry_price
- 止盈至少是止损的2倍

---

## ⚡ 输出要求

1. **严格JSON格式**，包含所有必填字段
2. **analysis字段必须包含**：
   - `multi_timeframe_trend`: 各周期趋势描述
   - `timeframe_confluence`: 多周期共振程度
   - `technical_signals`: 关键技术信号
   - `risk_assessment`: 风险评估
   - `stop_loss_rationale`: 止损逻辑（必须说明方向验证）
3. **reasoning字段**：一句话总结（50字内）
4. **confidence字段**：诚实评估，<50时必须hold

---

## 🚨 特别提醒

- ⚠️ **做空止损方向**：stop_loss_price **必须大于** entry_price
- ⚠️ **做多止损方向**：stop_loss_price **必须小于** entry_price
- ⚠️ **逆大周期重仓**：1h下跌时不允许开多仓>5%
- ⚠️ **极端指标规避**：RSI>80或<20时谨慎开仓
- ⚠️ **风险收益比**：必须≥2，否则不值得交易

现在请开始分析并输出JSON格式的决策。
"""
    
    def _get_fallback_decision(self, context: Dict) -> Dict:
        """
        获取兜底决策（当LLM失败时）
        
        返回保守的hold决策
        """
        return {
            'action': 'hold',
            'symbol': context.get('symbol', 'BTCUSDT'),
            'confidence': 0,
            'leverage': 1,
            'position_size_pct': 0,
            'stop_loss_pct': 1.0,
            'take_profit_pct': 2.0,
            'reasoning': 'LLM决策失败，采用保守策略观望',
            'timestamp': context.get('timestamp'),
            'is_fallback': True
        }
    
    def validate_decision(self, decision: Dict) -> bool:
        """
        验证决策格式是否正确
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'action', 'symbol', 'confidence', 'leverage',
            'position_size_pct', 'stop_loss_pct', 'take_profit_pct', 'reasoning'
        ]
        
        # 检查必需字段
        for field in required_fields:
            if field not in decision:
                log.error(f"决策缺少必需字段: {field}")
                return False
        
        # 检查action合法性
        valid_actions = [
            'open_long', 'open_short', 'close_position',
            'add_position', 'reduce_position', 'hold'
        ]
        if decision['action'] not in valid_actions:
            log.error(f"无效的action: {decision['action']}")
            return False
        
        # 检查数值范围
        if not (0 <= decision['confidence'] <= 100):
            log.error(f"confidence超出范围: {decision['confidence']}")
            return False
        
        if not (1 <= decision['leverage'] <= config.risk.get('max_leverage', 5)):
            log.error(f"leverage超出范围: {decision['leverage']}")
            return False
        
        if not (0 <= decision['position_size_pct'] <= 100):
            log.error(f"position_size_pct超出范围: {decision['position_size_pct']}")
            return False
        
        return True
