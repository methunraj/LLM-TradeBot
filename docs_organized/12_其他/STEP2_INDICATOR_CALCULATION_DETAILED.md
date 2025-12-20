# Step 2: 多周期技术指标计算详解

> **系统位置**: `src/data/processor.py` - `MarketDataProcessor.process_klines()`  
> **调用位置**: `run_live_trading.py` - 第197-199行  
> **版本**: processor_v2 (2025-12-18修正版)

---

## 📋 目录

1. [概述](#概述)
2. [输入数据](#输入数据)
3. [处理流程](#处理流程)
4. [技术指标详解](#技术指标详解)
5. [Warmup期设计](#warmup期设计)
6. [数据质量验证](#数据质量验证)
7. [输出数据](#输出数据)
8. [常见问题](#常见问题)

---

## 概述

**Step 2** 是技术指标计算的核心步骤，负责将Step 1获取的原始K线数据转换为包含14类、20+个技术指标的结构化DataFrame。

### 核心特性

✅ **多周期独立处理**  
- 5m、15m、1h三个时间周期各自独立计算
- 不存在重采样或周期间依赖关系
- 每个周期使用自己的原始K线数据

✅ **严格数据验证**  
- 只检测真正的数据错误（OHLC逻辑违反、缺失值等）
- **绝不修改价格数据**（MAD裁剪已移除）
- 保持市场波动的完整性

✅ **指标稳定性保证**  
- 105根K线warmup期（确保MACD完全收敛）
- 从300根数据中有效使用195根
- 符合金融工程最佳实践

---

## 输入数据

### 数据来源
```python
# 来自 Step 1 的多周期K线数据
{
    "klines_5m": [300根K线],   # 5m周期，独立获取
    "klines_15m": [300根K线],  # 15m周期，独立获取
    "klines_1h": [300根K线],   # 1h周期，独立获取
    "symbol": "BTCUSDT"
}
```

### K线数据结构
```python
# 每根K线包含11个字段
{
    "timestamp": "2025-12-17 23:35:00",  # 开盘时间（已转换）
    "open": 89833.44,                    # 开盘价 (USDT)
    "high": 89850.15,                    # 最高价 (USDT)
    "low": 89782.0,                      # 最低价 (USDT)
    "close": 89782.0,                    # 收盘价 (USDT)
    "volume": 7.65175,                   # 成交量 (BTC)
    "close_time": "2025-12-17 23:39:59", # 收盘时间
    "quote_volume": 687245.0624541,      # 成交额 (USDT)
    "trades": 2252,                      # 成交笔数
    "taker_buy_base": 5.21543,           # 主动买入量 (BTC)
    "taker_buy_quote": 468410.4785605    # 主动买入额 (USDT)
}
```

### 数据量要求
- **最小要求**: 50根（满足SMA_50计算）
- **实际配置**: 300根（确保指标稳定）
- **有效数据**: 195根（扣除105根warmup期）

---

## 处理流程

### 完整流程图
```
原始K线 (300根)
    ↓
【1. 数据验证与清洗】
    ├── KlineValidator.validate_and_clean_klines()
    ├── 检测: 缺失值/NaN/Inf/负数
    ├── 检测: OHLC逻辑违反
    ├── 检测: 时间序列问题
    └── 动作: 删除无效K线（不修改价格）
    ↓
有效K线 (≈295-300根)
    ↓
【2. DataFrame转换】
    ├── 时间戳转换: Unix毫秒 → datetime
    ├── 设置索引: timestamp
    └── 数据类型规范化
    ↓
【3. 技术指标计算】
    ├── 趋势指标: SMA_20, SMA_50, EMA_12, EMA_26
    ├── 动量指标: MACD, MACD_Signal, RSI
    ├── 波动指标: 布林带, ATR
    └── 成交量指标: Volume_SMA, VWAP, OBV
    ↓
【4. Warmup期标记】
    ├── 前105根: is_warmup=True, is_valid=False
    └── 第106根起: is_warmup=False, is_valid=True
    ↓
【5. 快照ID生成】
    └── snapshot_id = uuid4()[:8]
    ↓
【6. 缓存与归档】
    ├── 内存缓存: df_cache[symbol_timeframe]
    └── 文件归档: data/step2/YYYYMMDD/*.parquet
    ↓
完整DataFrame (300行 × 33列)
```

### 关键代码路径

#### 1. 数据验证
```python
# src/data/processor.py: 第71-90行
if validate:
    klines, validation_report = self.validator.validate_and_clean_klines(
        klines, 
        symbol,
        action='remove'  # ✅ 只删除无效数据，不修改价格
    )
    
    # 记录清洗详情
    anomaly_details = {
        'removed_count': validation_report.get('removed_count', 0),
        'issues': validation_report.get('issues', []),
        'method': validation_report.get('method', 'Integrity-Check-Only')
    }
```

#### 2. 指标计算入口
```python
# src/data/processor.py: 第112行
df = self._calculate_indicators(df)
```

#### 3. Warmup标记
```python
# src/data/processor.py: 第115行
df = self._mark_warmup_period(df)
```

---

## 技术指标详解

### 指标参数配置
```python
# src/data/processor.py: 第18-26行
INDICATOR_PARAMS = {
    'sma': [20, 50],
    'ema': [12, 26],
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'rsi': {'period': 14},
    'bollinger': {'period': 20, 'std_dev': 2},
    'atr': {'period': 14},
    'volume_sma': {'period': 20}
}
```

### 1. 移动平均线 (Trend Indicators)

#### SMA - Simple Moving Average
```python
# 简单移动平均（算术平均）
df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
```

**计算公式**:
```
SMA_20 = (Close[0] + Close[1] + ... + Close[19]) / 20
```

**作用**:
- SMA_20: 短期趋势，灵敏度高
- SMA_50: 中期趋势，稳定性好
- 金叉/死叉: SMA_20穿越SMA_50判断趋势转换

**有效期**: 第20根起（SMA_20），第50根起（SMA_50）

---

#### EMA - Exponential Moving Average
```python
# 指数移动平均（近期权重更大）
df['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
df['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()
```

**计算公式**:
```
α = 2 / (period + 1)
EMA[t] = α × Close[t] + (1 - α) × EMA[t-1]

EMA_12: α = 2/13 ≈ 0.1538
EMA_26: α = 2/27 ≈ 0.0741
```

**收敛理论**:
- **95%权重累积**: 需要 3×周期 根K线
- EMA_12: 3×12 = 36根起基本稳定
- EMA_26: 3×26 = 78根起基本稳定

**作用**:
- 比SMA更快响应价格变化
- MACD的基础组件

---

### 2. MACD - 移动平均收敛发散指标

#### ⚠️ 重要修正说明 (2025-12-18)
**问题**: 之前版本将MACD归一化为百分比形式，破坏了经典定义  
**修正**: 恢复为标准价差形式（USDT单位），符合技术分析规范

```python
# ✅ 经典MACD定义（价差，非百分比）
macd_indicator = MACD(close=df['close'])
df['macd'] = macd_indicator.macd()              # MACD线（USDT）
df['macd_signal'] = macd_indicator.macd_signal()  # 信号线（USDT）
df['macd_diff'] = macd_indicator.macd_diff()     # 柱状图（USDT）
```

**计算公式**:
```
MACD = EMA_12 - EMA_26  （价格差，单位: USDT）
Signal = EMA_9(MACD)    （信号线）
Histogram = MACD - Signal  （柱状图，反映MACD与信号线距离）
```

**收敛分析**:
- EMA_26稳定: 需要78根
- Signal (EMA_9 of MACD): 需要额外27根
- **MACD完全稳定**: 78 + 27 = **105根** ← 这是warmup期的依据！

**作用**:
- 趋势强度: MACD > 0 (看涨), MACD < 0 (看跌)
- 交叉信号: MACD穿越Signal线
- 柱状图扩大/缩小: 趋势加速/减速

**典型值范围** (BTCUSDT, close≈90000):
- MACD: -500 ~ +500 USDT
- Signal: -400 ~ +400 USDT
- Histogram: -200 ~ +200 USDT

**如需归一化**: 在Step 3特征工程中添加
```python
df['macd_pct'] = (df['macd'] / df['close']) * 100
```

---

### 3. RSI - 相对强弱指标

```python
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
```

**计算公式**:
```
上涨均值 = avg(max(0, Close[t] - Close[t-1])) over 14 periods
下跌均值 = avg(max(0, Close[t-1] - Close[t])) over 14 periods
RS = 上涨均值 / 下跌均值
RSI = 100 - (100 / (1 + RS))
```

**值域**: 0 ~ 100

**判断标准**:
- RSI > 70: 超买区（可能回调）
- RSI < 30: 超卖区（可能反弹）
- 50附近: 多空平衡

**有效期**: 第14根起

---

### 4. 布林带 (Bollinger Bands)

```python
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()   # 上轨
df['bb_middle'] = bb.bollinger_mavg()   # 中轨（SMA_20）
df['bb_lower'] = bb.bollinger_lband()   # 下轨
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
```

**计算公式**:
```
中轨 = SMA_20
标准差 = std(Close, 20)
上轨 = 中轨 + 2×标准差
下轨 = 中轨 - 2×标准差
宽度 = (上轨 - 下轨) / 中轨
```

**作用**:
- 价格通道: 95%的价格落在上下轨之间
- 波动性: 宽度扩大=波动增加，收窄=盘整
- 突破信号: 价格触及/突破上下轨

**典型值** (BTCUSDT, close≈90000):
- bb_width: 0.03 ~ 0.08（3% ~ 8%）
- 宽度<0.02: 低波动（盘整）
- 宽度>0.10: 高波动（趋势或震荡）

**有效期**: 第20根起

---

### 5. ATR - 平均真实波幅

#### ⚠️ ATR前期0值问题修复 (2025-12-18)
**问题**: ta库的ATR前13根默认为0，导致波动率指标失真  
**修正**: 使用True Range的EMA回填前期值

```python
# 先计算True Range
df['prev_close'] = df['close'].shift(1)
df['tr1'] = df['high'] - df['low']
df['tr2'] = abs(df['high'] - df['prev_close'])
df['tr3'] = abs(df['low'] - df['prev_close'])
df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

# 计算ATR
atr_indicator = AverageTrueRange(
    high=df['high'], low=df['low'], close=df['close'], window=14
)
df['atr'] = atr_indicator.average_true_range()

# ✅ 修复前13根ATR=0的问题
mask = df['atr'] == 0
if mask.any():
    tr_ema = df['true_range'].ewm(span=14, adjust=False).mean()
    df.loc[mask, 'atr'] = tr_ema[mask]
```

**计算公式**:
```
True Range = max(
    High - Low,
    |High - Prev_Close|,
    |Low - Prev_Close|
)
ATR = EMA_14(True Range)
```

**作用**:
- 波动率度量: ATR越大，波动越剧烈
- 止损设置: ATR × 2 作为止损距离
- 仓位管理: 高ATR降低杠杆

**典型值** (BTCUSDT, close≈90000):
- ATR: 300 ~ 600 USDT
- atr_pct = ATR / Close: 0.3% ~ 0.7%

**有效期**: 第1根起（修复后）

---

### 6. 成交量指标

#### Volume SMA & Ratio
```python
df['volume_sma'] = df['volume'].rolling(window=20).mean()
df['volume_ratio'] = np.where(
    (df['volume_sma'].notna()) & (df['volume_sma'] > 0),
    df['volume'] / df['volume_sma'],
    1.0  # 默认正常水平
)
```

**作用**:
- volume_ratio > 1.5: 放量（关注度上升）
- volume_ratio < 0.5: 缩量（市场冷清）
- 配合价格: 放量上涨=强势，缩量上涨=虚弱

---

#### VWAP - 成交量加权平均价

```python
window = 20
df['price_volume'] = df['close'] * df['volume']
rolling_pv = df['price_volume'].rolling(window=window).sum()
rolling_vol = df['volume'].rolling(window=window).sum()

df['vwap'] = np.where(
    rolling_vol > 0,
    rolling_pv / rolling_vol,
    df['close']  # 成交量为0时用close代替
)
```

**计算公式**:
```
VWAP_20 = Σ(Close × Volume)_20 / Σ(Volume)_20
```

**作用**:
- 机构成本线: VWAP代表主力平均成本
- 支撑/阻力: 价格围绕VWAP波动
- Close > VWAP: 买方占优
- Close < VWAP: 卖方占优

**有效期**: 第20根起

---

#### OBV - 能量潮指标

```python
df['obv'] = (df['volume'] * np.sign(df['close'].diff())).fillna(0).cumsum()
```

**计算公式**:
```
OBV[t] = OBV[t-1] + Volume[t] × sign(Close[t] - Close[t-1])

sign = +1 (价格上涨)
sign = -1 (价格下跌)
sign = 0  (价格不变)
```

**作用**:
- 资金流向: OBV上升=资金流入，下降=资金流出
- 背离信号: 价格新高但OBV不创新高（顶背离）

**有效期**: 第2根起

---

### 7. 价格变化指标

```python
df['price_change_pct'] = df['close'].pct_change() * 100
df['high_low_range'] = np.where(
    df['close'] > 0,
    (df['high'] - df['low']) / df['close'] * 100,
    0.0
)
```

**作用**:
- price_change_pct: 单根K线涨跌幅（%）
- high_low_range: 振幅（影线长度）

---

## Warmup期设计

### ✅ 关键修正 (2025-12-18)

**原问题**:
- 原warmup期设为50根，第51根起即认为is_valid=True
- 但MACD/Signal需要105根才能完全收敛
- 导致Step 4趋势判断基于未稳定的数据，产生错误信号

**修正方案**:
```python
# src/data/processor.py: _mark_warmup_period()

WARMUP_PERIOD = 105  # ✅ 从50提升至105

# 收敛分析:
# - EMA12: 3×12 = 36根
# - EMA26: 3×26 = 78根
# - MACD Signal (EMA9 of MACD): 78 + 27 = 105根
```

### Warmup期理论依据

#### EMA收敛公式
```
权重累积 = 1 - (1 - α)^n
当 n = 3×周期 时，权重累积 ≈ 95%

例如 EMA26:
α = 2/27 ≈ 0.0741
n = 3×26 = 78
权重累积 = 1 - (1 - 0.0741)^78 ≈ 95.2%
```

#### 各指标收敛时间
| 指标 | 周期 | 完全稳定所需K线数 | 备注 |
|------|------|------------------|------|
| SMA_20 | 20 | 20 | 简单平均，立即稳定 |
| SMA_50 | 50 | 50 | 简单平均，立即稳定 |
| EMA_12 | 12 | 36 | 3×12 |
| EMA_26 | 26 | 78 | 3×26 |
| MACD | - | 78 | 依赖EMA26 |
| Signal | 9 | 105 | 78 + 3×9 |
| RSI | 14 | 14 | 滚动窗口，立即稳定 |
| BB | 20 | 20 | 滚动窗口，立即稳定 |
| ATR | 14 | 14 | 滚动窗口，修复后立即稳定 |

**结论**: **105根**是确保所有指标稳定的最小值

### 标记逻辑

```python
# 前105根: warmup期
df.iloc[:105, 'is_warmup'] = True
df.iloc[:105, 'is_valid'] = False

# 第106根起: 有效期
df.iloc[105:, 'is_warmup'] = False
df.iloc[105:, 'is_valid'] = True
```

### 数据量分配

```
总数据: 300根
├── Warmup期: 105根 (35%)
└── 有效数据: 195根 (65%) ✅ 充足
```

**为什么300根?**
- 原limit=100，有效数据仅50根（100-50），不够用
- 提升至300，有效数据195根，足够支撑分析和回测
- 3-5倍最大周期（50×3=150，50×5=250），300根是保守策略

---

## 数据质量验证

### 1. 输入验证 (KlineValidator)

#### 检测项
```python
# ✅ 只检测真正的数据错误
- 缺失字段: open/high/low/close/volume
- 异常值: NaN / Inf / None
- 价格范围: < 0.001 或 > 10,000,000
- 负成交量: volume < 0
- OHLC逻辑: high < low, high < open, low > close
- 时间序列: 重复时间戳, 时间断档
```

#### ❌ 不处理的"异常"（正常市场行为）
```python
- ❌ 大幅跳空/涨跌幅（15%+）
- ❌ 长影线Pin Bar（20%+ High-Low Range）
- ❌ MAD统计偏离
- ❌ 连续单边行情
```

**核心原则**: K线是市场事实，绝不修改价格！

#### 处理方式
```python
action='remove'  # 删除无效K线
action='keep'    # 保留但标记（用于分析）
# ❌ 不支持 'clip', 'cap', 'smooth' 等修改价格的操作
```

### 2. 指标完整性检查

```python
# src/data/processor.py: check_indicator_completeness()

completeness = processor.check_indicator_completeness(df, min_coverage=0.95)

# 返回值
{
    'is_complete': True/False,
    'issues': [  # 问题列表
        'macd 包含 26 个NaN值 (覆盖率: 91.3%)',
        'sma_50 包含 49 个NaN值 (覆盖率: 83.7%)'
    ],
    'coverage': {  # 各指标覆盖率
        'sma_20': 0.937,
        'sma_50': 0.837,
        'ema_12': 0.967,
        'macd': 0.913,
        'rsi': 0.957,
        ...
    },
    'overall_coverage': 0.932  # 总体覆盖率
}
```

#### 关键指标列表
```python
critical_indicators = [
    'sma_20', 'sma_50', 'ema_12', 'ema_26',
    'macd', 'macd_signal', 'macd_diff',
    'rsi', 'bb_upper', 'bb_middle', 'bb_lower',
    'atr', 'volume_sma', 'volume_ratio'
]
```

#### 检查项
1. **指标存在性**: 列是否存在
2. **NaN计数**: NaN值数量和比例
3. **Inf检测**: 是否包含无穷大
4. **覆盖率**: 有效值 / 总数
5. **Warmup状态**: is_valid比例

### 3. 预期覆盖率（300根数据）

| 指标 | 有效数据 | 覆盖率 | 说明 |
|------|---------|--------|------|
| sma_20 | 281/300 | 93.7% | 前19根NaN |
| sma_50 | 251/300 | 83.7% | 前49根NaN |
| ema_12 | 290/300 | 96.7% | 前10根NaN（近似） |
| ema_26 | 274/300 | 91.3% | 前26根NaN（近似） |
| macd | 274/300 | 91.3% | 同EMA26 |
| rsi | 287/300 | 95.7% | 前13根NaN |
| bb系列 | 281/300 | 93.7% | 同SMA20 |
| atr | 300/300 | 100% | ✅ 修复后全覆盖 |

**总体覆盖率**: 约93-95%，符合预期

---

## 输出数据

### DataFrame结构

```python
# 300行 × 33列

"""
列名分类:

1. 基础数据 (11列):
   - timestamp (索引): datetime
   - open, high, low, close: float (USDT)
   - volume: float (BTC)
   - close_time: datetime
   - quote_volume: float (USDT)
   - trades: int
   - taker_buy_volume: float (BTC)
   - taker_buy_quote_volume: float (USDT)

2. 趋势指标 (4列):
   - sma_20, sma_50: float (USDT)
   - ema_12, ema_26: float (USDT)

3. 动量指标 (4列):
   - macd: float (USDT)
   - macd_signal: float (USDT)
   - macd_diff: float (USDT)
   - rsi: float (0-100)

4. 波动指标 (5列):
   - bb_upper, bb_middle, bb_lower: float (USDT)
   - bb_width: float (百分比小数形式)
   - atr: float (USDT)

5. 成交量指标 (4列):
   - volume_sma: float (BTC)
   - volume_ratio: float (倍数)
   - vwap: float (USDT)
   - obv: float (累积量)

6. 价格变化 (2列):
   - price_change_pct: float (%)
   - high_low_range: float (%)

7. 质量标记 (2列):
   - is_warmup: bool
   - is_valid: bool

8. 追踪标记 (1列):
   - snapshot_id: str (8位UUID)
"""
```

### 示例数据（最后一行）

```python
# 真实数据 2025-12-17 15:35:00
{
    "timestamp": Timestamp("2025-12-17 15:35:00"),
    "open": 89830.5,
    "high": 89850.15,
    "low": 89782.0,
    "close": 89782.0,
    "volume": 7.65175,
    "sma_20": 88693.91,
    "sma_50": 87730.11,
    "ema_12": 89382.77,
    "ema_26": 88676.75,
    "macd": 706.02,           # USDT (EMA12-EMA26)
    "macd_signal": 612.34,    # USDT
    "macd_diff": 93.68,       # USDT (Histogram)
    "rsi": 71.60,
    "bb_upper": 90883.57,
    "bb_middle": 88693.91,
    "bb_lower": 86504.25,
    "bb_width": 0.0494,       # 4.94%
    "atr": 379.21,
    "volume_sma": 8.12,
    "volume_ratio": 0.942,
    "vwap": 89274.26,
    "obv": 1234.56,
    "price_change_pct": -0.06,
    "high_low_range": 0.076,  # 0.076%
    "is_warmup": False,       # ✅ 第106根起
    "is_valid": True,         # ✅ 第106根起
    "snapshot_id": "e00cbc5f"
}
```

### 归档文件

```
data/step2/20251217/
├── step2_indicators_BTCUSDT_5m_20251217_233509_e00cbc5f.parquet
├── step2_indicators_BTCUSDT_15m_20251217_233509_a1b2c3d4.parquet
├── step2_indicators_BTCUSDT_1h_20251217_233509_f9e8d7c6.parquet
├── step2_stats_BTCUSDT_5m_20251217_233509_e00cbc5f.txt
├── step2_stats_BTCUSDT_15m_20251217_233509_a1b2c3d4.txt
└── step2_stats_BTCUSDT_1h_20251217_233509_f9e8d7c6.txt
```

**文件命名**:
```
step2_indicators_{symbol}_{timeframe}_{date}_{time}_{snapshot_id}.parquet
```

### 统计报告示例

```
=== Step 2 指标数据统计报告 ===
生成时间: 2025-12-17 23:35:09
交易对: BTCUSDT
周期: 5m
快照ID: e00cbc5f

数据规模:
- 总行数: 300
- 总列数: 33
- Warmup期: 105根
- 有效数据: 195根

指标覆盖率:
- sma_20: 93.7% (281/300)
- sma_50: 83.7% (251/300)
- ema_12: 96.7% (290/300)
- macd: 91.3% (274/300)
- rsi: 95.7% (287/300)
- atr: 100.0% (300/300) ✅

总体覆盖率: 93.2%

数据范围:
- 时间跨度: 2025-12-17 10:00:00 ~ 2025-12-17 15:35:00 (5.58小时)
- 价格范围: [87123.5, 90234.8] USDT
- 成交量: 总计 2345.67 BTC

质量评估: ✅ PASS
- 无NaN/Inf异常
- 覆盖率达标 (>90%)
- Warmup期完整
- 适合进行Step 3特征工程
```

---

## 常见问题

### Q1: 为什么MACD不是百分比形式？

**A**: 2025-12-18修正，恢复为经典价差定义（USDT单位）。

**原因**:
1. **标准定义**: 经典技术分析中MACD就是价格差（EMA12 - EMA26）
2. **跨周期一致**: 不同价格资产（BTC vs ETH）可比性更强
3. **归一化时机**: 应在Step 3特征工程中进行，而非Step 2

**如需百分比**: 在Step 3添加
```python
df['macd_pct'] = (df['macd'] / df['close']) * 100
```

---

### Q2: 为什么Warmup期是105根而不是50根？

**A**: MACD Signal需要105根才能完全收敛。

**计算依据**:
```
EMA26稳定: 3×26 = 78根
Signal (EMA9 of MACD): 3×9 = 27根
总计: 78 + 27 = 105根
```

**影响**:
- 有效数据从250根降至195根（300-105）
- 但确保所有指标完全稳定，避免Step 4产生错误信号

---

### Q3: ATR前期为什么会有0值？

**A**: ta库的默认行为，已在2025-12-18修复。

**修复方法**:
```python
# 用True Range的EMA回填前13根
mask = df['atr'] == 0
if mask.any():
    tr_ema = df['true_range'].ewm(span=14, adjust=False).mean()
    df.loc[mask, 'atr'] = tr_ema[mask]
```

现在ATR从第1根起就有有效值。

---

### Q4: 为什么不对价格进行MAD裁剪？

**A**: 市场波动是真实的，不应被统计方法修改。

**原问题**:
- MAD裁剪会将大幅波动（如闪崩、瀑布）裁剪为虚假的正常值
- 破坏K线的OHLC逻辑（High可能被裁到<Open）
- 导致技术指标失真

**现行策略**:
- 只删除真正的数据错误（OHLC违反、NaN/Inf等）
- 保留所有正常的市场波动（包括极端行情）
- 让技术指标基于真实数据计算

---

### Q5: snapshot_id有什么用？

**A**: 追踪数据一致性，确保多周期数据来自同一时刻。

**使用场景**:
1. **调试**: 追溯某个信号基于哪批数据
2. **回测**: 验证历史快照的指标计算
3. **多周期同步**: 确保5m/15m/1h是同一次获取

**已知问题**: snapshot_id缺乏上下文（symbol/timeframe），详见 `SNAPSHOT_ID_DESIGN_ISSUE.md`

---

### Q6: 如何判断数据质量是否合格？

**A**: 使用 `check_indicator_completeness()` 检查。

**合格标准**:
```python
completeness = processor.check_indicator_completeness(df, min_coverage=0.95)

# ✅ 合格条件
is_complete = (
    completeness['overall_coverage'] >= 0.95 and  # 总体覆盖率≥95%
    len(completeness['issues']) == 0 and          # 无严重问题
    df['is_valid'].sum() >= 195                   # 有效数据≥195根
)
```

**典型问题**:
- 覆盖率<90%: 数据量不足或计算错误
- issues包含"warm-up期未完成": Warmup期标记错误
- atr覆盖率<100%: 未应用ATR修复补丁

---

### Q7: 多周期数据是如何独立计算的？

**A**: 每个周期单独调用 `process_klines()`，不存在重采样。

**独立性保证**:
```python
# run_live_trading.py: 197-199
df_5m = processor.process_klines(klines_5m, symbol, '5m')   # 独立处理
df_15m = processor.process_klines(klines_15m, symbol, '15m')  # 独立处理
df_1h = processor.process_klines(klines_1h, symbol, '1h')    # 独立处理

# 三个DataFrame完全独立:
# - 不同的原始K线数据
# - 不同的技术指标计算
# - 不同的snapshot_id
```

**为什么不重采样？**
1. 数据完整性: 重采样需要5m数据足够多（1h需1200×5m）
2. 时间对齐: 重采样可能引入对齐误差
3. 性能优势: 直接获取更快，数据更可靠
4. 数据独立: 每个周期可独立验证质量

---

### Q8: 如何验证指标计算正确性？

**A**: 对比ta库文档和手工计算，检查边界值。

**验证步骤**:
```python
# 1. 读取数据
df = processor.process_klines(klines, 'BTCUSDT', '5m')

# 2. 检查MACD（第106根）
row = df.iloc[105]
print(f"EMA12: {row['ema_12']:.2f}")  # 应约等于close
print(f"EMA26: {row['ema_26']:.2f}")
print(f"MACD: {row['macd']:.2f}")     # 应等于 EMA12 - EMA26

# 3. 检查SMA
sma_20_manual = df['close'].iloc[86:106].mean()  # 第106根的SMA20
print(f"SMA20计算: {row['sma_20']:.2f}")
print(f"SMA20手工: {sma_20_manual:.2f}")  # 应相等

# 4. 检查RSI范围
assert 0 <= row['rsi'] <= 100, "RSI超出0-100范围"

# 5. 检查布林带逻辑
assert row['bb_lower'] <= row['bb_middle'] <= row['bb_upper'], "布林带顺序错误"
```

---

### Q9: 如何处理数据不足的情况？

**A**: 系统会拒绝处理，返回空DataFrame。

**检查逻辑**:
```python
# src/data/processor.py: 第93-100行
required_bars = max(self.INDICATOR_PARAMS['sma'])  # 50
if len(klines) < required_bars:
    log.error(f"K线数量不足: 需要>={required_bars}, 实际={len(klines)}")
    return pd.DataFrame()  # ❌ 返回空，不勉强计算
```

**建议**:
- 始终请求 300 根K线（limit=300）
- 如果交易所返回不足300根，检查symbol是否存在或刚上市

---

### Q10: 如何添加新的技术指标？

**A**: 遵循现有模式，在 `_calculate_indicators()` 中添加。

**步骤**:
```python
# 1. 更新 INDICATOR_PARAMS
INDICATOR_PARAMS = {
    # ...existing...
    'new_indicator': {'period': 10}
}

# 2. 在 _calculate_indicators() 中计算
def _calculate_indicators(self, df):
    # ...existing indicators...
    
    # 新增指标
    df['new_indicator'] = SomeIndicator(
        close=df['close'], 
        window=self.INDICATOR_PARAMS['new_indicator']['period']
    ).calculate()
    
    return df

# 3. 更新 check_indicator_completeness() 的 critical_indicators 列表
critical_indicators = [
    # ...existing...
    'new_indicator'
]

# 4. 更新 _mark_warmup_period() 的收敛计算（如果需要）
WARMUP_PERIOD = max(105, new_indicator_convergence_period)
```

---

## 总结

**Step 2** 是技术指标计算的核心，确保所有后续步骤（特征工程、趋势判断、信号生成）基于高质量、稳定的技术指标数据。

### 关键要点

✅ **多周期独立**: 5m/15m/1h各自计算，不重采样  
✅ **指标稳定性**: 105根warmup期，确保MACD完全收敛  
✅ **数据保真**: 只删除错误，不修改价格  
✅ **质量验证**: 覆盖率检查、NaN/Inf检测  
✅ **可追溯性**: snapshot_id追踪数据一致性  

### 最佳实践

1. **始终验证数据质量**: 使用 `check_indicator_completeness()`
2. **尊重warmup期**: 只使用 `is_valid=True` 的数据
3. **理解指标含义**: 参考本文档和ta库文档
4. **归一化在Step 3**: 不要在Step 2修改指标定义
5. **保留原始数据**: 归档所有step2输出，便于回溯

---

**文档版本**: v1.0  
**最后更新**: 2025-12-18  
**维护者**: AI Quant Trading System  
**相关文档**: 
- `DATA_FLOW_STRUCTURED.md` (完整数据流)
- `FIX_DATA_QUALITY_GATING.md` (质量门控设计)
- `SNAPSHOT_ID_DESIGN_ISSUE.md` (快照ID改进建议)
