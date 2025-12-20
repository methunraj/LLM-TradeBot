# 步骤2: 数据处理与技术指标计算详解

## 📍 步骤概述

将原始K线数据转换为包含31个技术指标的DataFrame，为后续交易决策提供数据基础。

---

## 📥 输入数据

```python
{
  "data_type": "List[Dict]",
  "k线数量": 100,
  "时间范围": "2025-12-16 18:30 ~ 2025-12-17 02:45",
  "价格范围": "86,443.02 ~ 87,977.43 USDT"
}
```

**输入字段（每根K线）:**
- timestamp, open, high, low, close, volume
- close_time, quote_volume, trades
- taker_buy_base, taker_buy_quote

---

## ⚙️ 处理流程（5个步骤）

### 1️⃣ 数据验证与清洗
```python
# 使用 validator.validate_and_clean_klines()
异常检测方法: MAD + Returns-based
处理方式: clip（裁剪到邻近值）
```

### 2️⃣ 转换为 DataFrame
```python
df = pd.DataFrame(klines)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)
```

### 3️⃣ 计算技术指标（6大类，21个指标）

#### A. 移动平均线（4个）
```python
# SMA - 简单移动平均
sma_20 = SMAIndicator(close=df['close'], window=20).sma_indicator()
sma_50 = SMAIndicator(close=df['close'], window=50).sma_indicator()

# EMA - 指数移动平均
ema_12 = EMAIndicator(close=df['close'], window=12).ema_indicator()
ema_26 = EMAIndicator(close=df['close'], window=26).ema_indicator()
```

**公式说明：**
- **SMA(N)** = (P1 + P2 + ... + PN) / N
- **EMA(N)** = Price × α + EMA(昨日) × (1-α)，其中 α = 2/(N+1)

**实际值（最后一根K线）:**
```
SMA(20) = 87,478.26 USDT
SMA(50) = 87,491.13 USDT
EMA(12) = 87,612.99 USDT
EMA(26) = 87,535.13 USDT
```

---

#### B. MACD 指标（3个）⭐ 重点

```python
# 原始 MACD（绝对值）
macd_indicator = MACD(close=df['close'], window_fast=12, window_slow=26, window_sign=9)
macd_raw = macd_indicator.macd()
macd_signal_raw = macd_indicator.macd_signal()
macd_diff_raw = macd_indicator.macd_diff()

# 归一化为百分比（修复高价位资产问题）
df['macd'] = (macd_raw / df['close']) * 100
df['macd_signal'] = (macd_signal_raw / df['close']) * 100
df['macd_diff'] = (macd_diff_raw / df['close']) * 100
```

**公式说明：**
1. **MACD Line** = EMA(12) - EMA(26)
2. **Signal Line** = EMA(MACD, 9)
3. **MACD Histogram** = MACD Line - Signal Line

**归一化公式：**
```
MACD% = (MACD绝对值 / 当前价格) × 100
```

**实际值（最后一根K线）:**
```
原始 MACD = 87,612.99 - 87,535.13 = 77.86 USDT
归一化 MACD = 77.86 / 87,906.29 × 100 = 0.0886%
```

**对比：**
| 资产 | 价格 | 原始MACD | 归一化MACD% |
|------|------|----------|-------------|
| BTC (8万) | 87,906 | 77.86 | 0.0886% |
| ETH (3千) | 3,000 | 15.00 | 0.5000% |

✅ **归一化后，不同价位资产的MACD可比**

---

#### C. RSI 指标（1个）

```python
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
```

**公式说明：**
```
RS = 平均涨幅 / 平均跌幅（14周期）
RSI = 100 - (100 / (1 + RS))
```

**解读：**
- RSI > 70: 超买区域
- RSI < 30: 超卖区域
- 50: 中性

**实际值：** RSI(14) = 65.04 → **偏强，接近超买**

---

#### D. 布林带（4个）

```python
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()       # 上轨
df['bb_middle'] = bb.bollinger_mavg()       # 中轨（SMA20）
df['bb_lower'] = bb.bollinger_lband()       # 下轨
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
```

**公式说明：**
```
中轨 = SMA(20)
上轨 = 中轨 + 2 × 标准差(20)
下轨 = 中轨 - 2 × 标准差(20)
带宽 = (上轨 - 下轨) / 中轨
```

**实际值：**
```
上轨: 87,946.46
中轨: 87,478.26
下轨: 87,010.06
带宽: 0.0107 (1.07%)
```

**解读：** 当前价格 87,906.29 接近上轨，显示**强势上涨**

---

#### E. ATR 波动率（1个）⭐ 重要修复

```python
# 计算 True Range
df['prev_close'] = df['close'].shift(1)
df['tr1'] = df['high'] - df['low']
df['tr2'] = abs(df['high'] - df['prev_close'])
df['tr3'] = abs(df['low'] - df['prev_close'])
df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

# 使用 ta 库计算 ATR
atr_indicator = AverageTrueRange(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    window=14
)
df['atr'] = atr_indicator.average_true_range()

# 修复前13根K线的ATR=0问题
mask = df['atr'] == 0
if mask.any():
    df.loc[mask, 'atr'] = df.loc[mask, 'true_range'].ewm(span=14, adjust=False).mean()
```

**公式说明：**
```
True Range = max(
    高 - 低,
    |高 - 昨收|,
    |低 - 昨收|
)
ATR(14) = True Range 的14周期EMA
```

**实际值：** ATR = 195.90 USDT (0.22%)

**解读：** 
- ATR < 0.3%: 低波动
- 0.3% < ATR < 0.5%: 正常波动
- ATR > 0.5%: 高波动

---

#### F. 成交量指标（2个）

```python
df['volume_sma'] = df['volume'].rolling(window=20).mean()
df['volume_ratio'] = df['volume'] / df['volume_sma']
```

**公式说明：**
```
成交量比率 = 当前成交量 / 成交量SMA(20)
```

**实际值：**
```
当前成交量: 0.29 BTC
成交量SMA: 62.44 BTC
成交量比率: 0.0046 (0.46%)
```

**解读：** ⚠️ **成交量严重萎缩**（仅为平均值的0.46%）

---

### 4️⃣ Warm-up 期标记

```python
def _mark_warmup_period(df):
    min_bars_needed = max(
        50,  # SMA50
        35,  # MACD (26 + 9)
        14   # ATR
    ) = 50
    
    df['is_valid'] = False
    df.iloc[50:, df.columns.get_loc('is_valid')] = True
    
    return df
```

**逻辑：**
- 前 50 根K线标记为 `is_valid = False`（指标不稳定）
- 第 51 根开始标记为 `is_valid = True`（可用于交易决策）

**统计：**
```
总K线数: 100
Warm-up期: 50 (前50根) ❌
有效数据: 50 (后50根) ✅
```

---

### 5️⃣ 生成快照ID

```python
snapshot_id = str(uuid.uuid4())[:8]  # 例如: 'e00cbc5f'
df['snapshot_id'] = snapshot_id
```

**作用：** 追踪数据一致性，便于审计和回测对比

---

## 📤 输出数据结构

### DataFrame 信息
```python
{
  "类型": "pandas.DataFrame",
  "形状": "(100, 31)",  # 100根K线 × 31个字段
  "索引": "DatetimeIndex (timestamp)",
  "快照ID": "e00cbc5f"
}
```

### 完整列名（31列）

#### 原始数据（11列）
1. open, high, low, close, volume
2. close_time, quote_volume, trades
3. taker_buy_base, taker_buy_quote, returns

#### 技术指标（18列）
4. sma_20, sma_50
5. ema_12, ema_26
6. macd, macd_signal, macd_diff
7. rsi
8. bb_upper, bb_middle, bb_lower, bb_width
9. atr
10. volume_sma, volume_ratio
11. vwap
12. price_change_pct, high_low_range

#### 元数据（2列）
13. is_valid, snapshot_id

---

## 📊 最后一根K线（完整示例）

```python
{
  "时间": "2025-12-16 18:45:00",
  "快照ID": "e00cbc5f",
  "是否有效": True,  # ✅ 可用于交易
  
  # 价格数据
  "开盘价": 87906.41,
  "最高价": 87906.41,
  "最低价": 87906.28,
  "收盘价": 87906.29,
  "成交量": 0.2898,  # BTC
  
  # 移动平均线
  "SMA(20)": 87478.26,
  "SMA(50)": 87491.13,
  "EMA(12)": 87612.99,
  "EMA(26)": 87535.13,
  
  # MACD（归一化百分比）
  "MACD": 0.088577,      # %
  "Signal": 0.015505,    # %
  "Diff": 0.073072,      # % (柱状图)
  
  # 动量指标
  "RSI(14)": 65.04,      # 偏强
  
  # 布林带
  "上轨": 87946.46,
  "中轨": 87478.26,
  "下轨": 87010.06,
  "带宽": 0.010704,      # 1.07%
  
  # 波动率
  "ATR": 195.90,         # USDT
  "ATR%": 0.22,          # % (低波动)
  
  # 成交量
  "成交量SMA": 62.4420,
  "成交量比率": 0.0046,  # 0.46% (极低！)
  
  # 价格变化
  "价格变化%": -0.00,
  "高低价差%": 0.00
}
```

---

## 📊 最近10根K线对比表

| 时间 | 收盘价 | SMA50 | RSI | MACD% | ATR | 有效 |
|------|--------|-------|-----|-------|-----|------|
| 18:00 | 87,385.38 | 87,356.94 | 48.24 | -0.0754 | 227.60 | ✅ |
| 18:05 | 87,449.10 | 87,377.07 | 50.69 | -0.0621 | 223.08 | ✅ |
| 18:10 | 87,487.57 | 87,397.62 | 52.16 | -0.0475 | 218.87 | ✅ |
| 18:15 | 87,347.35 | 87,407.73 | 46.69 | -0.0483 | 216.68 | ✅ |
| 18:20 | 87,411.57 | 87,418.74 | 49.31 | -0.0425 | 213.40 | ✅ |
| 18:25 | 87,396.59 | 87,428.76 | 48.71 | -0.0389 | 206.54 | ✅ |
| 18:30 | 87,717.89 | 87,445.25 | 59.98 | -0.0062 | 217.74 | ✅ |
| 18:35 | 87,796.76 | 87,462.48 | 62.18 | +0.0265 | 216.17 | ✅ |
| 18:40 | 87,906.41 | 87,478.45 | 65.05 | +0.0617 | 210.96 | ✅ |
| **18:45** | **87,906.29** | **87,491.13** | **65.04** | **+0.0886** | **195.90** | **✅** |

**趋势分析：**
- 价格：从 87,385 → 87,906 (+0.60%) ⬆️
- RSI：从 48 → 65（进入超买区） ⚠️
- MACD：从负转正（金叉） ✅
- ATR：逐渐降低（波动减小）

---

## 🔍 关键指标解读

### 1. 趋势判断
```python
if close > sma_20 > sma_50:
    trend = "强势上涨"  # ✅ 当前状态
elif close > sma_20:
    trend = "温和上涨"
elif close < sma_20 < sma_50:
    trend = "强势下跌"
else:
    trend = "震荡"
```

### 2. MACD 信号
```python
if macd > macd_signal and macd > 0:
    signal = "强势看多"  # ✅ 当前状态
elif macd > macd_signal:
    signal = "温和看多"
elif macd < macd_signal and macd < 0:
    signal = "强势看空"
else:
    signal = "温和看空"
```

### 3. 成交量确认
```python
if volume_ratio > 1.5:
    volume_status = "放量"
elif volume_ratio > 0.8:
    volume_status = "正常"
else:
    volume_status = "缩量"  # ⚠️ 当前状态（0.46%）
```

---

## ⚡ 性能指标

- **处理时间**: ~0.15秒
- **内存占用**: ~50 KB
- **计算复杂度**: O(n×m)，n=100行，m=31列

---

## 🎯 输出总结

| 项目 | 内容 |
|------|------|
| **数据类型** | pandas.DataFrame |
| **行数** | 100根K线 |
| **列数** | 31个字段 |
| **有效数据** | 50根（后50%） |
| **快照ID** | e00cbc5f |
| **主要指标** | SMA, EMA, MACD, RSI, BB, ATR, Volume |
| **特殊处理** | MACD归一化、ATR修复、Warm-up标记 |

---

## 🔄 下一步

此 DataFrame 将进入：

**步骤3: 特征提取**
- 从最后一行提取关键特征
- 计算趋势、动量、波动率
- 判断支撑阻力位
- 生成 LLM 输入

---

*Generated on 2025-12-17*
*Processor: MarketDataProcessor*
*Indicators: 21 technical indicators*
*Computation Time: ~150ms*
