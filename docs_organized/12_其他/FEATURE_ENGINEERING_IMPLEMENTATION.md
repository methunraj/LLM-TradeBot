# 特征工程实施文档

## 📋 概述

本文档说明 AI 交易系统中**真实特征工程管道**的实现细节、当前状态和未来集成路径。

### 实施背景

**问题：** 之前的 Step3 只是简单地复制和归一化 Step2 的指标，没有产生任何新的、有金融意义的高级特征。这导致：
- 浪费计算资源和存储空间
- 架构混乱（Step3 形同虚设）
- 无法支持机器学习模型或 LLM 策略

**解决方案：** 实施方案B - 构建真正的特征工程管道

---

## 🏗️ 架构设计

### 数据流

```
Step 1: 多周期K线获取
    ↓
Step 2: 技术指标计算 (31列)
    ↓
Step 3: 高级特征工程 (50+列) ← 本文档重点
    ↓
Step 4: 多周期上下文整合
    ↓
Step 5: 决策分析 (当前：基础规则策略)
    ↓
Step 6: 交易执行
```

### 模块结构

```
src/features/
├── technical_features.py  # 🆕 真实特征工程引擎
├── builder.py             # 原有：多周期上下文构建
└── __init__.py
```

---

## 🔧 实现细节

### 1. TechnicalFeatureEngineer 类

**位置：** `src/features/technical_features.py`

**核心方法：**
```python
class TechnicalFeatureEngineer:
    FEATURE_VERSION = 'v1.0'
    
    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于技术指标构建高级特征
        
        输入：Step2 的 DataFrame (31列技术指标)
        输出：扩展后的 DataFrame (31+50=81列)
        """
        # 1. 价格相对位置特征 (8个)
        # 2. 趋势强度特征 (10个)
        # 3. 动量特征 (8个)
        # 4. 波动率特征 (8个)
        # 5. 成交量特征 (8个)
        # 6. 组合特征 (8个)
```

### 2. 特征分类

#### A. 价格相对位置特征 (8个)

**金融意义：** 衡量当前价格在各种技术参考点的位置

| 特征名 | 公式 | 金融含义 |
|--------|------|----------|
| `price_to_sma20_pct` | `(close - sma_20) / sma_20 * 100` | 价格偏离20日均线的百分比 |
| `price_to_sma50_pct` | `(close - sma_50) / sma_50 * 100` | 价格偏离50日均线的百分比 |
| `price_to_ema12_pct` | `(close - ema_12) / ema_12 * 100` | 价格偏离EMA12的百分比 |
| `price_to_ema26_pct` | `(close - ema_26) / ema_26 * 100` | 价格偏离EMA26的百分比 |
| `bb_position` | `(close - bb_lower) / (bb_upper - bb_lower) * 100` | 价格在布林带中的位置 (0-100) |
| `price_to_vwap_pct` | `(close - vwap) / vwap * 100` | 价格偏离成交量加权均价 |
| `price_to_recent_high_pct` | `(close - high_20) / high_20 * 100` | 相对20期最高价的位置 |
| `price_to_recent_low_pct` | `(close - low_20) / low_20 * 100` | 相对20期最低价的位置 |

**应用场景：**
- 识别超买/超卖区域
- 判断支撑/阻力位突破
- 评估价格回归均值的可能性

---

#### B. 趋势强度特征 (10个)

**金融意义：** 衡量市场趋势的强度和方向

| 特征名 | 公式 | 金融含义 |
|--------|------|----------|
| `ema_cross_strength` | `(ema_12 - ema_26) / close * 100` | EMA快慢线交叉强度 |
| `sma_cross_strength` | `(sma_20 - sma_50) / close * 100` | SMA交叉强度 |
| `macd_momentum_5` | `macd - macd.shift(5)` | MACD的5期动量 |
| `macd_momentum_10` | `macd - macd.shift(10)` | MACD的10期动量 |
| `trend_alignment` | `sign(ema_cross) + sign(sma_cross)` | 双重趋势一致性 (-1/0/1) |
| `price_slope_5` | `polyfit(close, 5)[0] / close * 100` | 5期价格线性回归斜率 |
| `price_slope_10` | `polyfit(close, 10)[0] / close * 100` | 10期价格线性回归斜率 |
| `price_slope_20` | `polyfit(close, 20)[0] / close * 100` | 20期价格线性回归斜率 |
| `directional_strength` | `(up_days / total_days) * 100` | 方向性强度 (0-100) |

**应用场景：**
- 识别趋势方向和强度
- 判断趋势加速或减速
- 评估趋势持续性

---

#### C. 动量特征 (8个)

**金融意义：** 衡量价格变化的速度和加速度

| 特征名 | 公式 | 金融含义 |
|--------|------|----------|
| `rsi_momentum_5` | `rsi - rsi.shift(5)` | RSI的5期变化 |
| `rsi_momentum_10` | `rsi - rsi.shift(10)` | RSI的10期变化 |
| `rsi_zone_numeric` | `cut(rsi, bins=[0,30,40,60,70,100])` | RSI区域离散化 (-2到+2) |
| `return_1` | `close.pct_change(1) * 100` | 1期收益率 |
| `return_5` | `close.pct_change(5) * 100` | 5期收益率 |
| `return_10` | `close.pct_change(10) * 100` | 10期收益率 |
| `return_20` | `close.pct_change(20) * 100` | 20期收益率 |
| `momentum_acceleration` | `return_5 - return_5.shift(5)` | 动量加速度 |

**应用场景：**
- 识别动量强弱
- 判断超买/超卖
- 捕捉动量反转

---

#### D. 波动率特征 (8个)

**金融意义：** 衡量市场波动性和风险

| 特征名 | 公式 | 金融含义 |
|--------|------|----------|
| `atr_normalized` | `atr / close * 100` | ATR标准化（相对价格） |
| `bb_width_change` | `bb_width - bb_width.shift(5)` | 布林带宽度变化 |
| `bb_width_pct_change` | `bb_width.pct_change(5) * 100` | 布林带宽度变化率 |
| `volatility_5` | `close.pct_change().rolling(5).std() * 100` | 5期历史波动率 |
| `volatility_10` | `close.pct_change().rolling(10).std() * 100` | 10期历史波动率 |
| `volatility_20` | `close.pct_change().rolling(20).std() * 100` | 20期历史波动率 |
| `hl_range_ma5` | `high_low_range.rolling(5).mean()` | 高低点振幅5期均值 |
| `hl_range_expansion` | `high_low_range / hl_range_ma5` | 当前振幅相对均值 |

**应用场景：**
- 评估市场风险
- 识别波动率扩张/收缩
- 调整仓位大小

---

#### E. 成交量特征 (8个)

**金融意义：** 衡量市场参与度和资金流向

| 特征名 | 公式 | 金融含义 |
|--------|------|----------|
| `volume_trend_5` | `volume.rolling(5).mean() / volume_sma` | 5期成交量趋势 |
| `volume_trend_10` | `volume.rolling(10).mean() / volume_sma` | 10期成交量趋势 |
| `volume_change_pct` | `volume.pct_change() * 100` | 成交量变化率 |
| `volume_acceleration` | `volume_change_pct - volume_change_pct.shift(5)` | 成交量加速度 |
| `price_volume_trend` | `(volume * sign(close.diff())).rolling(20).sum()` | 价格-成交量趋势 |
| `obv_ma20` | `obv.rolling(20).mean()` | OBV的20期均值 |
| `obv_trend` | `(obv - obv_ma20) / obv_ma20 * 100` | OBV趋势指标 |
| `vwap_deviation_ma5` | `price_to_vwap_pct.rolling(5).mean()` | VWAP偏离的5期均值 |

**应用场景：**
- 识别主力资金流向
- 验证价格突破有效性
- 评估市场流动性

---

#### F. 组合特征 (8个)

**金融意义：** 多个指标的综合信号

| 特征名 | 公式 | 金融含义 | 取值范围 |
|--------|------|----------|----------|
| `trend_confirmation_score` | `sign(ema_cross) + sign(sma_cross) + sign(macd)` | 多指标趋势确认 | -3 到 +3 |
| `overbought_score` | `(rsi>70) + (bb_pos>80) + (price_to_sma20>5)` | 超买综合评分 | 0 到 3 |
| `oversold_score` | `(rsi<30) + (bb_pos<20) + (price_to_sma20<-5)` | 超卖综合评分 | 0 到 3 |
| `market_strength` | `abs(ema_cross) * volume_ratio * (1+atr_norm/100)` | 市场强度综合指标 | 浮点数 |
| `risk_signal` | `volatility_20 / volume_ratio` | 风险信号 | 浮点数 |
| `reversal_probability` | `(rsi_extreme)*2 + (bb_extreme)*2 + (macd_div)` | 反转可能性评分 | 0 到 5 |
| `trend_sustainability` | `abs(trend_score) * clip(vol_ratio) * (1-vol/10)` | 趋势持续性评分 | 浮点数 |

**应用场景：**
- 综合判断市场状态
- 评估交易风险
- 提供决策置信度

---

## 📊 特征重要性分组

### Critical（核心特征，8个）

**必须使用的关键特征：**

1. `price_to_sma20_pct` - 价格相对短期均线位置
2. `ema_cross_strength` - 短期趋势强度
3. `macd` - 动量方向
4. `rsi` - 超买超卖状态
5. `bb_position` - 价格在布林带位置
6. `trend_confirmation_score` - 综合趋势确认
7. `volume_ratio` - 成交量异常检测
8. `atr_normalized` - 波动率风险

**使用建议：**
- 机器学习模型的基础特征集
- LLM上下文的核心输入
- 规则策略的主要判断依据

### Important（重要特征，8个）

**建议使用的辅助特征：**

1. `price_to_sma50_pct` - 价格相对长期均线位置
2. `sma_cross_strength` - 长期趋势强度
3. `macd_momentum_5` - MACD变化速度
4. `rsi_momentum_5` - RSI变化速度
5. `volatility_20` - 中期波动率
6. `obv_trend` - 资金流向
7. `trend_sustainability` - 趋势可持续性
8. `market_strength` - 综合市场强度

**使用建议：**
- 提高模型预测准确率
- 增强决策置信度
- 辅助风险评估

### Supplementary（辅助特征，剩余）

**可选的补充特征：**
- 多周期收益率
- 波动率变化率
- 反转概率评分
- 其他组合指标

**使用建议：**
- 特定市场环境下的专用特征
- 模型ensemble的多样性来源
- 深度分析的补充维度

---

## 🚀 集成路径

### 当前状态（2025-01）

**已实现：**
- ✅ `TechnicalFeatureEngineer` 类完全实现
- ✅ 50+ 特征的计算逻辑
- ✅ 在 `run_live_trading.py` 中集成（Step3）
- ✅ 特征数据自动归档（Parquet格式）
- ✅ 特征统计报告生成

**未集成：**
- ⏳ Step5 决策逻辑仍使用基础指标（trend、RSI）
- ⏳ 高级特征仅用于数据积累，未用于实际决策

**数据状态：**
```
data/step3/
└── YYYYMMDD/
    ├── step3_features_BTCUSDT_5m_*_v1.0.parquet  # 特征数据
    └── step3_features_BTCUSDT_5m_*_stats.json    # 统计报告
```

---

### 未来路径 1：机器学习策略

#### 1.1 数据准备

```python
import pandas as pd
from pathlib import Path

# 读取历史特征数据
feature_files = Path('data/step3').glob('**/*.parquet')
df_features = pd.concat([pd.read_parquet(f) for f in feature_files])

# 加载特征重要性分组
from src.features.technical_features import TechnicalFeatureEngineer
engineer = TechnicalFeatureEngineer()
critical_features = engineer.get_feature_importance_groups()['critical']

# 准备训练数据
X = df_features[critical_features]
```

#### 1.2 标签生成

```python
# 方法1：基于未来收益率
df_features['future_return_10'] = df_features['close'].shift(-10).pct_change(10)
df_features['label'] = pd.cut(
    df_features['future_return_10'],
    bins=[-float('inf'), -0.5, 0.5, float('inf')],
    labels=['SELL', 'HOLD', 'BUY']
)

# 方法2：基于当前规则策略的历史信号
# 读取 step6 的历史决策
decision_files = Path('data/step6').glob('**/*.json')
labels = [json.load(open(f))['signal'] for f in decision_files]
```

#### 1.3 模型训练

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 评估
accuracy = model.score(X_test, y_test)
print(f"模型准确率: {accuracy:.2%}")
```

#### 1.4 集成到决策逻辑

```python
# 修改 run_live_trading.py 的 analyze_market() 方法

def analyze_market(self, market_state: Dict) -> str:
    # 原有规则策略
    rule_signal = self._rule_based_strategy(market_state)
    
    # 新增：机器学习策略
    features_5m = market_state['features']['5m']  # Step3的特征
    ml_features = features_5m[critical_features].iloc[-1].values.reshape(1, -1)
    ml_signal = self.ml_model.predict(ml_features)[0]
    ml_confidence = self.ml_model.predict_proba(ml_features).max()
    
    # 策略融合
    if ml_confidence > 0.8:  # 高置信度，使用ML信号
        return ml_signal
    else:  # 低置信度，回退到规则策略
        return rule_signal
```

---

### 未来路径 2：LLM 增强策略

#### 2.1 特征上下文构建

```python
def build_llm_context(features: pd.DataFrame) -> str:
    """将特征转换为LLM可理解的文本"""
    latest = features.iloc[-1]
    
    # 核心特征解读
    context = f"""
    ## 市场状态分析（基于高级特征）
    
    ### 趋势分析
    - 趋势确认分数: {latest['trend_confirmation_score']}/3
      {'强烈上涨' if latest['trend_confirmation_score'] >= 2 else 
       '强烈下跌' if latest['trend_confirmation_score'] <= -2 else '震荡'}
    - EMA交叉强度: {latest['ema_cross_strength']:.2f}%
    - 价格斜率(20期): {latest['price_slope_20']:.2f}%
    
    ### 动量分析
    - RSI: {latest['rsi']:.1f} (动量5期: {latest['rsi_momentum_5']:.1f})
    - 10期收益率: {latest['return_10']:.2f}%
    - 动量加速度: {latest['momentum_acceleration']:.2f}
    
    ### 风险评估
    - 超买评分: {latest['overbought_score']}/3
    - 超卖评分: {latest['oversold_score']}/3
    - 波动率(20期): {latest['volatility_20']:.2f}%
    - 风险信号: {latest['risk_signal']:.2f}
    
    ### 市场强度
    - 综合强度: {latest['market_strength']:.2f}
    - 成交量趋势: {latest['volume_trend_5']:.2f}
    - OBV趋势: {latest['obv_trend']:.2f}%
    
    ### 预测指标
    - 反转可能性: {latest['reversal_probability']}/5
    - 趋势持续性: {latest['trend_sustainability']:.2f}
    
    基于以上特征，请分析当前市场状态并给出交易建议。
    """
    
    return context
```

#### 2.2 LLM 决策集成

```python
from openai import OpenAI

def analyze_market_with_llm(self, market_state: Dict) -> str:
    # 构建特征上下文
    features = market_state['features']['5m']
    context = build_llm_context(features)
    
    # 调用LLM
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一个专业的量化交易分析师"},
            {"role": "user", "content": context}
        ]
    )
    
    # 解析LLM输出
    analysis = response.choices[0].message.content
    
    # 提取信号（BUY/SELL/HOLD）
    if 'BUY' in analysis.upper():
        return 'BUY'
    elif 'SELL' in analysis.upper():
        return 'SELL'
    else:
        return 'HOLD'
```

---

### 未来路径 3：混合策略

**设计理念：**
- 规则策略作为基准（快速、可解释）
- ML模型提供置信度评分（数据驱动）
- LLM提供深度分析（全局理解）

```python
def analyze_market_hybrid(self, market_state: Dict) -> Dict:
    # 1. 规则策略（当前实现）
    rule_signal = self._rule_based_strategy(market_state)
    
    # 2. 机器学习评分
    ml_signal, ml_confidence = self._ml_strategy(market_state)
    
    # 3. LLM分析
    llm_analysis = self._llm_strategy(market_state)
    
    # 4. 投票机制
    signals = {
        'rule': rule_signal,
        'ml': ml_signal if ml_confidence > 0.7 else 'HOLD',
        'llm': llm_analysis['signal']
    }
    
    # 多数投票
    from collections import Counter
    final_signal = Counter(signals.values()).most_common(1)[0][0]
    
    # 5. 置信度计算
    agreement = sum(1 for s in signals.values() if s == final_signal)
    confidence = agreement / len(signals) * 100
    
    return {
        'signal': final_signal,
        'confidence': confidence,
        'breakdown': signals,
        'ml_confidence': ml_confidence,
        'llm_reasoning': llm_analysis['reasoning']
    }
```

---

## 📈 性能考虑

### 计算开销

**特征工程耗时：**
- 300行数据：~50-100ms
- 主要开销：rolling计算、polyfit

**优化建议：**
1. 使用增量计算（只计算最新行）
2. 缓存中间结果（rolling windows）
3. 使用 NumPy 向量化操作

### 存储开销

**单个文件大小：**
- Parquet格式：~50-100KB（195行 × 81列）
- 每天3个文件（5m主周期）：~150-300KB/天
- 年度存储：~50-100MB/年

**优化建议：**
1. 使用 Parquet 压缩（已实现）
2. 定期归档历史数据
3. 只保存关键特征（critical + important）

---

## 🧪 测试和验证

### 功能测试

```python
# 测试特征工程
python test_feature_engineering.py

# 验证特征数量
assert len(engineer.feature_names) == 50

# 验证特征无NaN
assert features.isnull().sum().sum() == 0

# 验证特征版本
assert features.attrs['feature_version'] == 'v1.0'
```

### 回测验证

```python
# 使用历史数据验证特征有效性
from src.backtest import Backtester

backtester = Backtester()
results = backtester.run(
    features=critical_features,
    strategy='ml',
    start_date='2024-01-01',
    end_date='2025-01-01'
)

print(f"收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
```

---

## 📝 总结

### 已完成

✅ **架构层面：**
- 真实特征工程管道实现
- 50+ 金融意义明确的高级特征
- 特征重要性分组
- 数据归档和统计报告

✅ **代码层面：**
- `TechnicalFeatureEngineer` 类完整实现
- 集成到 `run_live_trading.py`（Step3）
- 特征元数据追踪（版本、数量、名称）

✅ **数据层面：**
- 历史特征数据积累
- Parquet 高效存储
- 统计报告自动生成

### 待完成

⏳ **决策集成：**
- Step5 使用高级特征（当前仍用基础指标）
- 机器学习模型训练和部署
- LLM 上下文增强

⏳ **测试验证：**
- 特征有效性回测
- 模型性能评估
- A/B测试对比

⏳ **文档更新：**
- ~~DATA_FLOW_STRUCTURED.md~~ ✅ 已更新
- 集成示例代码
- 最佳实践指南

### 下一步行动

1. **短期（立即）：**
   - 创建特征工程测试脚本
   - 验证特征数据质量
   - 更新架构问题文档

2. **中期（1-2周）：**
   - 积累足够的历史特征数据（>=1个月）
   - 开发ML模型原型
   - 评估特征对决策的贡献

3. **长期（1-3个月）：**
   - 将ML模型集成到决策逻辑
   - 实施混合策略
   - 上线A/B测试

---

## 🔗 相关文档

- [数据流转详解](DATA_FLOW_STRUCTURED.md)
- [架构问题汇总](ARCHITECTURE_ISSUES_SUMMARY.md)
- [Warmup期修复](WARMUP_INSUFFICIENT_FIX.md)
- [K线验证逻辑](KLINE_VALIDATION_FIX.md)

---

**文档版本：** v1.0  
**最后更新：** 2025-01-22  
**维护者：** AI Trader Development Team
