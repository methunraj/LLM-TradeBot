# 技术指标计算逻辑详解

## 📍 核心文件位置

**主要计算函数**：`src/data/processor.py` 中的 `MarketDataProcessor` 类

- **入口函数**：`process_klines()` - 处理K线并计算所有指标
- **指标计算**：`_calculate_indicators()` - 具体计算逻辑
- **预热标记**：`_mark_warmup_period()` - 标记前期不稳定数据

## 🎯 指标计算参数（固化配置）

```python
INDICATOR_PARAMS = {
    'sma': [20, 50],                          # 简单移动平均线周期
    'ema': [12, 26],                          # 指数移动平均线周期
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},  # MACD参数
    'rsi': {'period': 14},                    # RSI周期
    'bollinger': {'period': 20, 'std_dev': 2}, # 布林带参数
    'atr': {'period': 14},                    # ATR周期
    'volume_sma': {'period': 20}              # 成交量均线周期
}
```

## 📊 各指标计算详解

### 1️⃣ 移动平均线 (SMA & EMA)

**位置**：`src/data/processor.py:151-154`

```python
# 简单移动平均线
df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()

# 指数移动平均线
df['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
df['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()
```

**说明**：
- SMA20：最近20根K线收盘价的算术平均
- SMA50：最近50根K线收盘价的算术平均
- EMA12：12期指数移动平均，对近期价格赋予更高权重
- EMA26：26期指数移动平均

**用途**：判断趋势方向，支撑/阻力位

---

### 2️⃣ MACD（移动平均收敛散度）

**位置**：`src/data/processor.py:156-169`

```python
macd_indicator = MACD(close=df['close'])
macd_raw = macd_indicator.macd()           # MACD线 = EMA12 - EMA26
macd_signal_raw = macd_indicator.macd_signal()  # 信号线 = MACD的9期EMA
macd_diff_raw = macd_indicator.macd_diff()     # 柱状图 = MACD - Signal

# ⚠️ 关键优化：归一化为百分比
# 原因：BTC价格在8-9万，原始MACD数值过大不便比较
df['macd'] = (macd_raw / df['close']) * 100        # 转为相对价格的百分比
df['macd_signal'] = (macd_signal_raw / df['close']) * 100
df['macd_diff'] = (macd_diff_raw / df['close']) * 100
```

**关键改进**：
- **归一化处理**：MACD / Price × 100，转为百分比
- **好处**：使指标在不同价位下可比（BTC 8万 vs 5万时都在 ±1% 范围内）
- **未归一化问题**：原始MACD在高价位会有几百甚至上千的异常大数值

**输出范围**：通常在 -1% ~ +1% 之间

**用途**：
- MACD > Signal：金叉，看涨信号
- MACD < Signal：死叉，看跌信号

---

### 3️⃣ RSI（相对强弱指标）

**位置**：`src/data/processor.py:171`

```python
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
```

**计算逻辑**：
1. 计算14期价格变化
2. 分离涨幅和跌幅
3. RSI = 100 - (100 / (1 + RS))，其中 RS = 平均涨幅 / 平均跌幅

**输出范围**：0 ~ 100
- RSI > 70：超买区域，可能回调
- RSI < 30：超卖区域，可能反弹
- RSI ≈ 50：中性

**用途**：判断市场是否过热或过冷

---

### 4️⃣ 布林带 (Bollinger Bands)

**位置**：`src/data/processor.py:173-183`

```python
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()     # 上轨 = SMA20 + 2×标准差
df['bb_middle'] = bb.bollinger_mavg()     # 中轨 = SMA20
df['bb_lower'] = bb.bollinger_lband()     # 下轨 = SMA20 - 2×标准差

# 布林带宽度（安全计算，避免除0）
df['bb_width'] = np.where(
    df['bb_middle'] > 0,
    (df['bb_upper'] - df['bb_lower']) / df['bb_middle'],
    np.nan
)
```

**计算逻辑**：
- 中轨 = 20期简单移动平均
- 上轨 = 中轨 + 2倍标准差
- 下轨 = 中轨 - 2倍标准差
- 带宽 = (上轨 - 下轨) / 中轨

**用途**：
- 价格触及上轨：超买
- 价格触及下轨：超卖
- 带宽收窄：波动率降低，可能突破
- 带宽扩大：波动率增加

---

### 5️⃣ ATR（平均真实波动幅度）

**位置**：`src/data/processor.py:185-208`

```python
# 计算真实波动幅度
df['prev_close'] = df['close'].shift(1)
df['tr1'] = df['high'] - df['low']                    # 当日高低差
df['tr2'] = abs(df['high'] - df['prev_close'])        # 当日高与前收盘差
df['tr3'] = abs(df['low'] - df['prev_close'])         # 当日低与前收盘差
df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)  # 取最大值

# 使用 ta 库计算 ATR（14期平均）
atr_indicator = AverageTrueRange(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    window=14
)
df['atr'] = atr_indicator.average_true_range()

# ⚠️ 修复前期 ATR=0 问题
mask = df['atr'] == 0
if mask.any():
    tr_ema = df['true_range'].ewm(span=14, adjust=False).mean()
    df.loc[mask, 'atr'] = tr_ema[mask]
```

**关键改进**：
- **修复前期0值问题**：前13根K线 ATR 会为0，用 True Range 的 EMA 填充
- **更稳定**：确保所有K线都有有效的波动率指标

**用途**：
- 衡量市场波动性
- 设置止损止盈位（如：止损 = 当前价 - 2×ATR）

---

### 6️⃣ 成交量指标

**位置**：`src/data/processor.py:210-218`

```python
# 成交量20期均线
df['volume_sma'] = df['volume'].rolling(window=20).mean()

# 成交量比率（安全计算，避免除0）
df['volume_ratio'] = np.where(
    (df['volume_sma'].notna()) & (df['volume_sma'] > 0),
    df['volume'] / df['volume_sma'],
    1.0  # 默认值1表示正常水平
)
```

**用途**：
- volume_ratio > 1.5：成交量放大，可能突破
- volume_ratio < 0.5：成交量萎缩，观望为主

---

### 7️⃣ VWAP（成交量加权平均价）

**位置**：`src/data/processor.py:220-231`

```python
# 使用20期滚动窗口（修复原有全局累积逻辑）
window = 20
df['price_volume'] = df['close'] * df['volume']
rolling_pv = df['price_volume'].rolling(window=window).sum()
rolling_vol = df['volume'].rolling(window=window).sum()

# 安全计算，避免除0
df['vwap'] = np.where(
    rolling_vol > 0,
    rolling_pv / rolling_vol,
    df['close']  # 成交量为0时用close代替
)
```

**改进**：
- **原逻辑问题**：全局累积 VWAP 会随时间持续上升/下降，失去参考意义
- **新逻辑**：使用20期滚动窗口，更符合量化策略需求

**用途**：
- 价格 > VWAP：多方占优
- 价格 < VWAP：空方占优

---

### 8️⃣ 价格变化指标

**位置**：`src/data/processor.py:233-241`

```python
# 价格变化百分比
df['price_change_pct'] = df['close'].pct_change() * 100

# 高低点振幅（安全计算）
df['high_low_range'] = np.where(
    df['close'] > 0,
    (df['high'] - df['low']) / df['close'] * 100,
    0.0
)
```

**用途**：
- price_change_pct：单根K线涨跌幅
- high_low_range：单根K线振幅，衡量日内波动

---

## ⏰ Warm-up 期标记

**位置**：`src/data/processor.py:243-278`

```python
def _mark_warmup_period(self, df: pd.DataFrame) -> pd.DataFrame:
    """标记指标预热期"""
    
    # 计算所需最小K线数
    min_bars_needed = max(
        max(self.INDICATOR_PARAMS['sma']),      # 50
        self.INDICATOR_PARAMS['macd']['slow'] + 
        self.INDICATOR_PARAMS['macd']['signal'],  # 26 + 9 = 35
        self.INDICATOR_PARAMS['atr']['period']  # 14
    )  # = 50
    
    # 标记有效数据
    df['is_valid'] = False
    if len(df) > min_bars_needed:
        df.iloc[min_bars_needed:, df.columns.get_loc('is_valid')] = True
    
    return df
```

**逻辑**：
- SMA50 需要 50 根K线才稳定
- MACD 需要 26 + 9 = 35 根
- ATR 需要 14 根
- **取最大值 = 50**
- 前50根K线标记为 `is_valid=False`（预热期，指标不稳定）

**重要性**：
- 避免使用不稳定的指标做交易决策
- 回测时应过滤掉 `is_valid=False` 的数据

---

## 🔧 辅助函数

### 安全除法

```python
def _safe_div(self, numer, denom, eps=1e-9, fill=0.0):
    """避免除以0或极小值导致 inf/NaN"""
    small = denom.abs() < eps
    denom_safe = denom.copy()
    denom_safe[small] = eps
    res = numer / denom_safe
    res[small] = fill
    return res
```

### 极值截断

```python
def _winsorize(self, s, lower_q=0.01, upper_q=0.99):
    """按分位数截断极端值"""
    lo = s.quantile(lower_q)
    hi = s.quantile(upper_q)
    return s.clip(lower=lo, upper=hi)
```

### 时间缺口检查

```python
def _check_time_gaps(self, df, freq_minutes=5, allowed_gap_bars=2):
    """检测并填充小的时间缺口"""
    # 只对 ≤2 根K线的缺口进行线性插值
    # 更大的缺口保留 NaN（避免虚假数据）
```

---

## 📊 完整数据流

```
原始K线数据 (List[Dict])
    ↓
数据验证与清洗 (DataValidator)
    ↓ (异常值 clip/drop)
转为 DataFrame
    ↓
计算技术指标 (_calculate_indicators)
    ├─ SMA/EMA
    ├─ MACD (归一化)
    ├─ RSI
    ├─ 布林带
    ├─ ATR (修复0值)
    ├─ 成交量指标
    ├─ VWAP (滚动窗口)
    └─ 价格变化
    ↓
标记 Warm-up 期 (_mark_warmup_period)
    ↓ (前50根标记为 is_valid=False)
生成快照ID
    ↓
返回完整 DataFrame
```

---

## ✅ 数据质量保证

### 1. 异常值处理
- **方法**：MAD（中位数绝对偏差）检测
- **阈值**：MAD > 5.0 视为异常
- **处理**：clip（截断到邻近值）而非 drop（删除）

### 2. 安全计算
- 所有除法操作使用 `_safe_div` 或 `np.where` 避免除0
- 空值处理：优先用合理默认值而非 NaN

### 3. 归一化
- MACD 归一化为价格百分比（-1% ~ +1%）
- 高低点振幅转为百分比
- 成交量比率（相对均值）

### 4. 预热期标记
- 前50根K线不用于交易决策
- 回测时必须过滤

---

## 🔍 调试与验证

### 查看指标计算日志

```bash
# 日志会输出：
# - 处理K线数量
# - 使用的参数
# - 异常值检测结果
# - Warm-up 标记统计
# - 快照ID和价格
```

### 查看统计报告

```bash
# Step2 统计报告位置
data/step2/YYYYMMDD/step2_stats_BTCUSDT_5m_*.txt

# 包含：
# - 各指标的有效值比例
# - 均值、标准差、最小值、最大值
# - 缺失值和无穷值统计
```

### 查看原始数据

```python
import pandas as pd

# 读取 Parquet 文件
df = pd.read_parquet('data/step2/20251217/step2_indicators_*.parquet')

# 查看指标列
print(df.columns.tolist())

# 查看最新数据
print(df.tail())

# 查看 RSI 分布
print(df['rsi'].describe())

# 检查 MACD 范围（应该在 ±1% 左右）
print(df[['macd', 'macd_signal', 'macd_diff']].describe())
```

---

## 📚 相关文档

- [ta-lib Python 文档](https://technical-analysis-library-in-python.readthedocs.io/)
- [技术分析指标详解](https://www.investopedia.com/technical-analysis-4689657)
- [DataSaver 使用指南](DATA_SAVER_USAGE.md)

---

🎯 **关键要点总结**：
1. 所有指标在 `_calculate_indicators()` 中计算
2. MACD 已归一化为百分比（重要改进）
3. ATR 前期0值已修复
4. 前50根K线是预热期（`is_valid=False`）
5. 所有除法操作都有安全保护
6. 数据质量通过 DataValidator 保证
