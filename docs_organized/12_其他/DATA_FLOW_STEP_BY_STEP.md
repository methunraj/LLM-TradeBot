# AI 量化交易系统数据流转 - 分步详解

## 📊 概述

本文档按照**输入 → 处理逻辑 → 输出**的格式，详细描述每个步骤的数据流转。

---

## Step 0: 系统初始化

### 📥 输入
```python
{
    'config': TRADING_CONFIG,        # 交易配置
    'api_key': os.getenv('API_KEY'), # API 密钥
    'api_secret': os.getenv('API_SECRET')
}
```

### ⚙️ 处理逻辑
**位置**: `run_live_trading.py: LiveTradingBot.__init__()`

```python
1. 初始化 Binance 客户端 (API 连接)
2. 初始化数据处理器 (MarketDataProcessor)
3. 初始化特征构建器 (FeatureBuilder)
4. 初始化风险管理器 (RiskManager)
5. 初始化执行引擎 (ExecutionEngine)
6. 实例化数据保存器 (DataSaver)
7. 获取账户余额
```

### 📤 输出
```python
{
    'bot': LiveTradingBot 实例,
    'balance': 139.31,              # 账户余额 (USDT)
    'status': 'initialized'
}
```

---

## Step 1: 获取原始K线数据

### 📥 输入
```python
{
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'limit': 100
}
```

### ⚙️ 处理逻辑
**位置**: `src/api/binance_client.py: get_klines()`

```python
1. 调用 Binance API: GET /fapi/v1/klines
2. 解析返回的原始数据 (嵌套列表)
3. 转换为字典格式:
   {
       'timestamp': int(kline[0]),
       'open': float(kline[1]),
       'high': float(kline[2]),
       'low': float(kline[3]),
       'close': float(kline[4]),
       'volume': float(kline[5]),
       'close_time': int(kline[6]),
       'quote_volume': float(kline[7]),
       'trades': int(kline[8]),
       'taker_buy_volume': float(kline[9]),
       'taker_buy_quote_volume': float(kline[10])
   }
4. 对 5m/15m/1h 三个周期重复执行
5. 保存到 DataSaver (step1)
```

**关键代码**:
```python
# run_live_trading.py: 119-125
klines_5m = self.client.get_klines(symbol, '5m', limit=100)
klines_15m = self.client.get_klines(symbol, '15m', limit=100)
klines_1h = self.client.get_klines(symbol, '1h', limit=100)

self.data_saver.save_step1_klines(klines_5m, symbol, '5m')
```

### 📤 输出

**数据结构** (100根K线):
```python
[
    {
        'timestamp': 1734451500000,          # Unix 毫秒时间戳
        'open': 89500.0,
        'high': 89600.0,
        'low': 89400.0,
        'close': 89550.0,
        'volume': 42.5,                      # 成交量 (BTC)
        'close_time': 1734451799999,
        'quote_volume': 3806875.0,           # 成交额 (USDT)
        'trades': 850,
        'taker_buy_volume': 21.3,
        'taker_buy_quote_volume': 1903438.0
    },
    ... (共100根)
]
```

**归档文件**:
```
data/step1/20251217/
├── step1_klines_BTCUSDT_5m_20251217_233509.json     (33.4 KB) ← 含元数据
├── step1_klines_BTCUSDT_5m_20251217_233509.csv      (13.6 KB)
├── step1_klines_BTCUSDT_5m_20251217_233509.parquet  (17.3 KB)
└── step1_stats_BTCUSDT_5m_20251217_233509.txt       (2.1 KB)  ← 统计报告
```

---

## Step 2: 计算技术指标

### 📥 输入
```python
{
    'klines': [...],              # Step1 的 K线列表 (100根)
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'validate': True              # 是否启用数据验证
}
```

### ⚙️ 处理逻辑
**位置**: `src/data/processor.py: process_klines()`

#### 2.1 数据验证与清洗
```python
# src/data/validator.py: validate_and_clean_klines()
1. 检测异常值 (MAD 方法):
   - 计算中位数绝对偏差 (MAD)
   - 阈值: MAD > 5.0 标记为异常
   
2. 处理异常值 (clip 模式):
   - 计算邻域中位数 (前后5根K线)
   - 将异常值裁剪到邻域中位数
   
3. 生成验证报告:
   - 原始异常数、清洗后异常数
   - clipped 数量、dropped 数量
   - 异常详情 (index, field, value, reason)
```

#### 2.2 转换为 DataFrame
```python
# src/data/processor.py: 42-60
df = pd.DataFrame(klines)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df = df.set_index('timestamp')
df = df.sort_index()  # 确保时间顺序
```

#### 2.3 计算技术指标
**位置**: `src/data/processor.py: _calculate_indicators()`

```python
指标计算顺序:

1. SMA (简单移动平均) - 第151-152行
   sma_20 = close.rolling(window=20).mean()
   sma_50 = close.rolling(window=50).mean()

2. EMA (指数移动平均) - 第153-154行
   ema_12 = close.ewm(span=12, adjust=False).mean()
   ema_26 = close.ewm(span=26, adjust=False).mean()

3. MACD (移动平均收敛发散) - 第156-169行
   ⚠️ 重要改进: 归一化处理
   macd_raw = ema_12 - ema_26
   macd = (macd_raw / close) * 100           # 转换为百分比
   macd_signal = macd.ewm(span=9).mean()
   macd_hist = macd - macd_signal
   macd_diff = macd_hist                      # 别名

4. RSI (相对强弱指数) - 第171行
   rsi = ta.momentum.RSIIndicator(close, window=14).rsi()

5. 布林带 (Bollinger Bands) - 第173-183行
   bb_middle = sma_20
   bb_std = close.rolling(window=20).std()
   bb_upper = bb_middle + (2 * bb_std)
   bb_lower = bb_middle - (2 * bb_std)
   bb_width = (bb_upper - bb_lower) / bb_middle * 100

6. ATR (平均真实波幅) - 第185-208行
   ⚠️ 重要改进: 修复前期0值问题
   true_range = max(
       high - low,
       abs(high - prev_close),
       abs(low - prev_close)
   )
   atr = true_range.ewm(span=14, adjust=False).mean()
   # 对 ATR=0 的行，用 True Range 的 EMA 填充
   atr_pct = (atr / close) * 100

7. 成交量指标 - 第210-218行
   volume_sma = volume.rolling(window=20).mean()
   volume_ratio = volume / volume_sma (安全除法)

8. VWAP (成交量加权平均价) - 第220-231行
   ⚠️ 重要改进: 使用滚动窗口而非全局累积
   typical_price = (high + low + close) / 3
   price_volume = typical_price * volume
   vwap = price_volume.rolling(20).sum() / volume.rolling(20).sum()

9. OBV (能量潮) - 未明确实现

10. 价格变化 - 第233-241行
    price_change_pct = close.pct_change() * 100
    high_low_range = (high - low) / close * 100
```

#### 2.4 标记预热期
```python
# src/data/processor.py: _mark_warmup_period()
warmup_bars = 50  # 配置参数
df['is_warmup'] = df.index < df.index[warmup_bars]
df['is_valid'] = ~df['is_warmup']
```

#### 2.5 生成快照ID
```python
# src/data/processor.py: 108-138
snapshot_id = hashlib.md5(
    f"{symbol}_{timeframe}_{timestamp}".encode()
).hexdigest()[:8]

last_snapshot_data = {
    'snapshot_id': snapshot_id,
    'timestamp': df.iloc[-1].name,
    'close': float(df.iloc[-1]['close']),
    'volume': float(df.iloc[-1]['volume']),
    'n_bars_used': len(df)
}
```

#### 2.6 保存数据
```python
# run_live_trading.py: 133-135
self.data_saver.save_step2_indicators(
    df_5m, symbol, '5m', 
    snapshot_id='unknown',  # TODO: 使用实际的 snapshot_id
    save_stats=True
)
```

### 📤 输出

**DataFrame 结构** (100行 × 31列):

| 列类型 | 列名 | 说明 |
|--------|------|------|
| **基础OHLCV (11列)** | timestamp, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_volume, taker_buy_quote_volume | 原始K线数据 |
| **趋势指标 (6列)** | sma_20, sma_50, ema_12, ema_26, macd, macd_signal | 移动平均和MACD |
| **动量指标 (1列)** | rsi | 相对强弱指数 |
| **波动率指标 (5列)** | bb_upper, bb_middle, bb_lower, bb_width, atr | 布林带和ATR |
| **成交量指标 (3列)** | volume_sma, volume_ratio, vwap | 成交量分析 |
| **其他 (5列)** | macd_hist, macd_diff, atr_pct, price_change_pct, high_low_range | 衍生指标 |
| **质量标记 (2列)** | is_warmup, is_valid | 数据质量标记 |

**数据示例** (最后一行):
```python
{
    'timestamp': Timestamp('2025-12-17 15:35:00'),
    'close': 89782.0,
    'rsi': 71.60,
    'macd': 0.152,              # 已归一化 (%)
    'macd_signal': 0.135,
    'macd_hist': 0.017,
    'bb_upper': 90883.57,
    'bb_middle': 87485.62,
    'bb_lower': 86478.03,
    'bb_width': 5.04,           # (%)
    'atr': 163.44,
    'atr_pct': 0.182,           # (%)
    'volume_ratio': 0.51,
    'is_warmup': False,
    'is_valid': True
}
```

**归档文件**:
```
data/step2/20251217/
├── step2_indicators_BTCUSDT_5m_20251217_233509_unknown.parquet (28.5 KB)
└── step2_stats_BTCUSDT_5m_20251217_233509_unknown.txt          (3.8 KB)
```

**统计报告内容**:
```
- 数据质量: 总列数、缺失值、无穷值、预热期数据
- 关键指标统计: rsi, macd, bb, atr 等的均值、标准差、分位数
```

---

## Step 3: 提取特征快照

### 📥 输入
```python
{
    'df': DataFrame,              # Step2 的技术指标 DataFrame
    'symbol': 'BTCUSDT',
    'timeframe': '5m'
}
```

### ⚙️ 处理逻辑
**位置**: `src/features/builder.py: build_features()`

#### 3.1 特征提取
```python
# src/features/builder.py: 20-80

1. 价格特征 (4个):
   - price_change_pct (直接复制)
   - high_low_range (直接复制)
   - close_to_sma20_ratio = (close - sma_20) / sma_20 * 100
   - close_to_ema12_ratio = (close - ema_12) / ema_12 * 100

2. 趋势特征 (6个):
   - macd (直接复制)
   - macd_signal (直接复制)
   - macd_hist (直接复制)
   - ema_12 (需归一化)
   - ema_26 (需归一化)
   - sma_20 (需归一化)

3. 动量特征 (1个):
   - rsi (直接复制，已是0-100范围)

4. 波动率特征 (5个):
   - bb_upper (需归一化)
   - bb_middle (需归一化)
   - bb_lower (需归一化)
   - bb_width (直接复制，已是百分比)
   - atr_pct (直接复制，已是百分比)

5. 成交量特征 (3个):
   - volume_ratio (直接复制)
   - obv (如果存在)
   - vwap (需归一化)

6. 布林带位置 (1个):
   - bb_position = (close - bb_lower) / (bb_upper - bb_lower) * 100
```

#### 3.2 特征归一化
```python
# src/features/builder.py: 82-120

归一化公式: normalized_value = value / current_price

需要归一化的特征:
- ema_12_norm = ema_12 / close
- ema_26_norm = ema_26 / close
- sma_20_norm = sma_20 / close
- bb_upper_norm = bb_upper / close
- bb_middle_norm = bb_middle / close
- bb_lower_norm = bb_lower / close
- vwap_norm = vwap / close

不需要归一化的特征 (已是百分比或比率):
- rsi, macd, macd_signal, macd_hist
- bb_width, atr_pct, volume_ratio
- price_change_pct, high_low_range
- close_to_sma20_ratio, close_to_ema12_ratio
```

#### 3.3 数据质量标记
```python
# src/features/builder.py: 122-145

1. is_feature_valid:
   检查所有特征列是否包含 NaN 或 Inf
   is_feature_valid = not (has_nan or has_inf)

2. has_time_gap:
   检查相邻K线的时间间隔是否异常
   expected_gap = {'5m': 300, '15m': 900, '1h': 3600}
   time_diff = current_ts - prev_ts
   has_time_gap = time_diff > expected_gap * 1.5

3. is_warmup:
   从 step2 复制
```

#### 3.4 保存特征
```python
# run_live_trading.py: 141-143
self.data_saver.save_step3_features(
    features_5m, symbol, '5m',
    source_snapshot_id='unknown',
    feature_version='v1',
    save_stats=True
)
```

### 📤 输出

**DataFrame 结构** (100行 × ~25列):

| 特征组 | 特征列 | 数据类型 | 范围 |
|--------|--------|----------|------|
| **价格** | price_change_pct, high_low_range, close_to_sma20_ratio, close_to_ema12_ratio | float | % |
| **趋势** | macd, macd_signal, macd_hist, ema_12_norm, ema_26_norm, sma_20_norm | float | 归一化 |
| **动量** | rsi | float | 0-100 |
| **波动率** | bb_upper_norm, bb_middle_norm, bb_lower_norm, bb_width, bb_position, atr_pct | float | 归一化/% |
| **成交量** | volume_ratio, obv, vwap_norm | float | 归一化 |
| **质量** | is_feature_valid, has_time_gap, is_warmup | bool | - |

**数据示例** (最后一行):
```python
{
    'timestamp': Timestamp('2025-12-17 15:35:00'),
    'price_change_pct': 0.31,
    'high_low_range': 0.37,
    'close_to_sma20_ratio': 2.64,
    'close_to_ema12_ratio': 0.13,
    'macd': 0.152,
    'macd_signal': 0.135,
    'macd_hist': 0.017,
    'rsi': 71.60,
    'ema_12_norm': 1.0001,        # 归一化后接近1
    'ema_26_norm': 1.0003,
    'sma_20_norm': 0.9738,
    'bb_upper_norm': 1.0123,
    'bb_middle_norm': 0.9738,
    'bb_lower_norm': 0.9634,
    'bb_width': 5.04,
    'bb_position': 54.23,
    'atr_pct': 0.182,
    'volume_ratio': 0.51,
    'vwap_norm': 0.9998,
    'is_feature_valid': True,
    'has_time_gap': False,
    'is_warmup': False
}
```

**归档文件**:
```
data/step3/20251217/
├── step3_features_BTCUSDT_5m_20251217_233509_v1.parquet (22.1 KB)
└── step3_stats_BTCUSDT_5m_20251217_233509_v1.txt        (4.2 KB)
```

---

## Step 4: 构建多周期上下文

### 📥 输入
```python
{
    'symbol': 'BTCUSDT',
    'multi_timeframe_states': {
        '5m': {
            'price': 89782.0,
            'rsi': 71.60,
            'macd': 0.152,
            'macd_signal': 0.135,
            'trend': 'uptrend'
        },
        '15m': {...},  # 同样结构
        '1h': {...}    # 同样结构
    },
    'snapshot': {
        'price': {'price': 89782.0},
        'funding': {'funding_rate': 0},
        'oi': {},
        'orderbook': {}
    },
    'position_info': None
}
```

### ⚙️ 处理逻辑
**位置**: `src/features/builder.py: build_market_context()`

#### 4.1 提取各周期关键指标
```python
# run_live_trading.py: _extract_key_indicators()

def _extract_key_indicators(df) -> Dict:
    latest = df.iloc[-1]
    
    return {
        'price': float(latest['close']),
        'rsi': float(latest.get('rsi', 0)),
        'macd': float(latest.get('macd', 0)),
        'macd_signal': float(latest.get('macd_signal', 0)),
        'trend': _determine_trend(df)
    }

def _determine_trend(df) -> str:
    latest = df.iloc[-1]
    sma_20 = latest.get('sma_20', 0)
    sma_50 = latest.get('sma_50', 0)
    price = latest['close']
    
    if sma_20 > sma_50 and price > sma_20:
        return 'uptrend'
    elif sma_20 < sma_50 and price < sma_20:
        return 'downtrend'
    else:
        return 'sideways'
```

#### 4.2 构建综合上下文
```python
# src/features/builder.py: build_market_context()

market_context = {
    'symbol': symbol,
    'current_price': snapshot['price']['price'],
    'timeframes': multi_timeframe_states,
    'snapshot': snapshot,
    'position_info': position_info
}
```

#### 4.3 保存上下文
```python
# run_live_trading.py: 150-152
self.data_saver.save_step4_context(
    market_state, symbol, '5m',
    snapshot_id='unknown'
)
```

### 📤 输出

**数据结构**:
```python
{
    'symbol': 'BTCUSDT',
    'current_price': 89782.0,
    'timeframes': {
        '5m': {
            'price': 89782.0,
            'rsi': 71.60,
            'macd': 0.152,
            'macd_signal': 0.135,
            'trend': 'uptrend'
        },
        '15m': {
            'price': 89782.0,
            'rsi': 75.48,
            'macd': 0.143,
            'macd_signal': 0.128,
            'trend': 'uptrend'
        },
        '1h': {
            'price': 89782.0,
            'rsi': 73.11,
            'macd': 0.098,
            'macd_signal': 0.082,
            'trend': 'uptrend'
        }
    },
    'snapshot': {
        'price': {'price': 89782.0},
        'funding': {'funding_rate': 0},
        'oi': {},
        'orderbook': {}
    },
    'position_info': None
}
```

**归档文件**:
```
data/step4/20251217/
└── step4_context_BTCUSDT_5m_20251217_233510_unknown.json (1.5 KB)
```

---

## Step 5: 格式化 Markdown 文本

### 📥 输入
```python
{
    'market_state': {...},     # Step4 的市场上下文
    'symbol': 'BTCUSDT',
    'signal': 'HOLD'           # 预生成的信号
}
```

### ⚙️ 处理逻辑
**位置**: `run_live_trading.py` (内联代码，第154-176行)

```python
1. 提取数据:
   - 当前价格
   - 各周期趋势 (5m/15m/1h)
   - 各周期 RSI
   - 统计上涨/下跌周期数

2. 格式化为 Markdown:
   - 使用 f-string 模板
   - 包含标题、表格、列表
   - 展示交易信号和决策依据

3. 保存 Markdown:
   self.data_saver.save_step5_markdown(
       markdown_text, symbol, '5m',
       snapshot_id='live'
   )
```

**关键代码**:
```python
# run_live_trading.py: 154-176
timeframes = market_state.get('timeframes', {})
current_price = market_state.get('current_price', 0)

# 提取各周期数据
trend_5m = timeframes.get('5m', {}).get('trend', 'unknown')
trend_15m = timeframes.get('15m', {}).get('trend', 'unknown')
trend_1h = timeframes.get('1h', {}).get('trend', 'unknown')
rsi_5m = timeframes.get('5m', {}).get('rsi', 50)
rsi_15m = timeframes.get('15m', {}).get('rsi', 50)
rsi_1h = timeframes.get('1h', {}).get('rsi', 50)

# 统计趋势
uptrend_count = sum([
    trend_5m == 'uptrend',
    trend_15m == 'uptrend',
    trend_1h == 'uptrend'
])
downtrend_count = sum([
    trend_5m == 'downtrend',
    trend_15m == 'downtrend',
    trend_1h == 'downtrend'
])

# 生成 Markdown
markdown_text = f"""# 市场分析报告
            
## 交易对信息
- **交易对**: {symbol}
- **当前价格**: ${current_price:,.2f}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 多周期趋势分析
- **5分钟**: {trend_5m} (RSI: {rsi_5m:.1f})
- **15分钟**: {trend_15m} (RSI: {rsi_15m:.1f})
- **1小时**: {trend_1h} (RSI: {rsi_1h:.1f})

## 趋势统计
- 上涨周期数: {uptrend_count}/3
- 下跌周期数: {downtrend_count}/3

## 交易信号
**{signal}**

## 决策依据
- 趋势不明确，继续观望
"""
```

### 📤 输出

**Markdown 文本**:
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

## 交易信号
**HOLD**

## 决策依据
- 趋势不明确，继续观望
```

**归档文件**:
```
data/step5/20251217/
├── step5_llm_input_BTCUSDT_5m_20251217_233510_live.md   (0.8 KB)
└── step5_stats_BTCUSDT_5m_20251217_233510_live.txt      (0.5 KB)
```

**统计报告内容**:
```
- 总字符数
- 总行数
- 总字节数
- 内容预览（前500字符）
```

---

## Step 6: 生成交易决策

### 📥 输入
```python
{
    'market_state': {
        'timeframes': {
            '5m': {'trend': 'uptrend', 'rsi': 71.6},
            '15m': {'trend': 'uptrend', 'rsi': 75.5},
            '1h': {'trend': 'uptrend', 'rsi': 73.1}
        }
    }
}
```

### ⚙️ 处理逻辑
**位置**: `run_live_trading.py: generate_signal()`

```python
决策规则:

1. 买入信号 (BUY):
   条件1: uptrend_count >= 2 (至少2个周期上涨)
   AND
   条件2: rsi_1h < 70 (1小时RSI不超买)
   AND
   条件3: rsi_15m < 75 (15分钟RSI不严重超买)

2. 卖出信号 (SELL):
   条件1: downtrend_count >= 2 (至少2个周期下跌)
   OR
   条件2: (rsi_5m > 80 AND rsi_15m > 75) (严重超买)

3. 观望信号 (HOLD):
   其他所有情况
```

**关键代码**:
```python
# run_live_trading.py: 208-234
def generate_signal(self, market_state: Dict) -> str:
    timeframes = market_state.get('timeframes', {})
    
    # 获取各周期趋势
    trend_5m = timeframes.get('5m', {}).get('trend', 'unknown')
    trend_15m = timeframes.get('15m', {}).get('trend', 'unknown')
    trend_1h = timeframes.get('1h', {}).get('trend', 'unknown')
    
    # 获取RSI
    rsi_5m = timeframes.get('5m', {}).get('rsi', 50)
    rsi_15m = timeframes.get('15m', {}).get('rsi', 50)
    rsi_1h = timeframes.get('1h', {}).get('rsi', 50)
    
    # 多周期趋势一致性检查
    uptrend_count = sum([
        trend_5m == 'uptrend',
        trend_15m == 'uptrend',
        trend_1h == 'uptrend'
    ])
    
    downtrend_count = sum([
        trend_5m == 'downtrend',
        trend_15m == 'downtrend',
        trend_1h == 'downtrend'
    ])
    
    # 买入信号
    if uptrend_count >= 2 and rsi_1h < 70 and rsi_15m < 75:
        return 'BUY'
    
    # 卖出信号
    if downtrend_count >= 2 or (rsi_5m > 80 and rsi_15m > 75):
        return 'SELL'
    
    # 观望信号
    return 'HOLD'
```

**决策记录**:
```python
# run_live_trading.py: 178-183
decision_data = {
    'signal': signal,
    'confidence': 0,  # TODO: 计算信心度
    'analysis': {
        'trend_5m': trend_5m,
        'trend_15m': trend_15m,
        'trend_1h': trend_1h,
        'rsi_5m': rsi_5m,
        'rsi_15m': rsi_15m,
        'rsi_1h': rsi_1h,
        'uptrend_count': uptrend_count,
        'downtrend_count': downtrend_count
    },
    'timestamp': datetime.now().isoformat()
}

self.data_saver.save_step6_decision(
    decision_data, symbol, '5m', snapshot_id='live'
)
```

### 📤 输出

**决策结构**:
```python
{
    'signal': 'HOLD',
    'confidence': 0,
    'analysis': {
        'trend_5m': 'uptrend',
        'trend_15m': 'uptrend',
        'trend_1h': 'uptrend',
        'rsi_5m': 71.60,
        'rsi_15m': 75.48,
        'rsi_1h': 73.11,
        'uptrend_count': 3,
        'downtrend_count': 0
    },
    'timestamp': '2025-12-17T23:35:10.134048',
    'reason': '虽然三个周期都是上涨趋势，但RSI都在70+超买区域，避免追高'
}
```

**归档文件**:
```
data/step6/20251217/
├── step6_decision_BTCUSDT_5m_20251217_233510_live.json (0.6 KB)
└── step6_stats_BTCUSDT_5m_20251217_233510_live.txt     (0.4 KB)
```

---

## Step 7: 执行交易

### 📥 输入
```python
{
    'signal': 'SELL',           # 必须是 BUY 或 SELL (HOLD会跳过)
    'market_state': {
        'current_price': 89782.0,
        'timeframes': {...}
    }
}
```

### ⚙️ 处理逻辑
**位置**: `run_live_trading.py: execute_trade()`

#### 7.1 前置检查
```python
# 第251-265行
1. 检查信号 (跳过 HOLD)
   if signal == 'HOLD':
       return False

2. 获取当前价格
   current_price = market_state.get('current_price', 0)
   if current_price == 0:
       return False

3. 计算交易金额
   balance = get_account_balance()
   trade_amount = min(
       max_position_size,
       balance * (position_pct / 100)
   )

4. 检查最小名义金额（✅ 动态获取 - 重要改进）
   # 从交易所API动态获取最小名义金额要求
   MIN_NOTIONAL = client.get_symbol_min_notional(symbol)
   if MIN_NOTIONAL == 0:
       MIN_NOTIONAL = 5.0  # 无法获取时使用保守默认值
   
   # 检查名义价值（保证金 × 杠杆）
   notional_value = trade_amount * leverage
   if notional_value < MIN_NOTIONAL:
       print(f"⚠️ 名义价值 ${notional_value:.2f} 低于要求 ${MIN_NOTIONAL:.2f}")
       return False

5. 计算交易数量
   quantity = trade_amount / current_price
```

#### 7.2 用户确认
```python
# 第267-281行
if confirm_before_trade:
    print(f"\n⚠️ 即将执行真实交易！")
    print(f"信号: {signal}")
    print(f"价格: ${current_price:,.2f}")
    print(f"数量: {quantity:.6f} BTC")
    print(f"金额: ${trade_amount:,.2f} USDT")
    print(f"杠杆: {leverage}x")
    print(f"请在{confirm_seconds}秒内按 Ctrl+C 取消...")
    time.sleep(confirm_seconds)
```

#### 7.3 构建决策
```python
# 第283-309行
if signal == 'BUY':
    decision = {
        'action': 'open_long',
        'symbol': 'BTCUSDT',
        'position_size_pct': 80,
        'leverage': 1,
        'take_profit_pct': 2,
        'stop_loss_pct': 1
    }
else:  # SELL
    decision = {
        'action': 'open_short',
        'symbol': 'BTCUSDT',
        'position_size_pct': 80,
        'leverage': 1,
        'take_profit_pct': 2,
        'stop_loss_pct': 1
    }
```

#### 7.4 执行订单
```python
# 第311-326行
result = self.execution_engine.execute_decision(
    decision=decision,
    account_info={'available_balance': balance},
    position_info=None,
    current_price=current_price
)

# ExecutionEngine 内部流程:
1. RiskManager.calculate_position_size()
   - 检查账户余额
   - 计算实际仓位大小
   - 应用杠杆
   
2. RiskManager.calculate_stop_levels()
   - 计算止损价格
   - 计算止盈价格
   
3. BinanceClient.place_market_order()
   - 下市价单
   - 同时下止损止盈单
   - 返回订单结果
```

#### 7.5 记录交易
```python
# 第328-369行
if result and result.get('success'):
    # 1. 使用 trade_logger 记录开仓
    trade_logger.log_open_position(
        symbol='BTCUSDT',
        side='LONG' / 'SHORT',
        decision=decision,
        execution_result=result,
        market_state=market_state,
        account_info={'available_balance': balance}
    )
    
    # 2. 保存到交易历史
    self.trade_history.append({
        'time': datetime.now().isoformat(),
        'signal': signal,
        'price': current_price,
        'quantity': quantity,
        'amount': trade_amount,
        'order_id': result.get('order_id')
    })
    self._save_trade_history()
    
    # 3. 归档到 step9 (⚠️ 新增功能)
    trade_event = {
        'trade_id': result.get('order_id'),
        'timestamp': datetime.now().isoformat(),
        'signal': signal,
        'price': current_price,
        'quantity': quantity,
        'amount': trade_amount,
        'order_id': result.get('order_id'),
        'success': True,
        'decision': decision,
        'execution_result': result,
        'market_state_snapshot': {
            'current_price': market_state.get('current_price'),
            'timeframes': market_state.get('timeframes')
        },
        'account_info': {'available_balance': balance}
    }
    self.data_saver.save_step9_trade_event(
        trade_event, 
        symbol=symbol, 
        timeframe=timeframe,
        trade_id=result.get('order_id')
    )
    
    return True
```

### 📤 输出

**执行结果**:
```python
{
    'success': True,
    'order_id': 'ORD_20251217_001',
    'symbol': 'BTCUSDT',
    'side': 'SHORT',
    'quantity': 0.001,
    'price': 89782.0,
    'total_value': 111.45,
    'fee': 0.11,
    'status': 'filled',
    'filled_time': '2025-12-17T23:35:15',
    'leverage': 1,
    'stop_loss_order': {
        'order_id': 'SL_20251217_001',
        'stop_price': 88884.18,  # -1%
        'trigger': 'MARK_PRICE'
    },
    'take_profit_order': {
        'order_id': 'TP_20251217_001',
        'stop_price': 91577.64,  # +2%
        'trigger': 'MARK_PRICE'
    }
}
```

**归档文件**:
```
data/step7/20251217/
├── step7_execution_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json
└── step7_executions_BTCUSDT_5m.csv

data/step9/20251217/
├── step9_trade_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json
├── step9_trades_BTCUSDT_5m_20251217.csv
└── step9_trades_BTCUSDT_5m_20251217.parquet
```

---

## Step 8: 回测分析

### 📥 输入
```python
{
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'start_date': '20251201',
    'end_date': '20251217',
    'strategy_version': 'v1'
}
```

### ⚙️ 处理逻辑
**位置**: (未在实盘使用，仅用于历史数据回测)

```python
1. 加载历史K线数据
2. 重放数据，模拟交易执行
3. 记录每笔交易的 entry/exit
4. 计算绩效指标:
   - total_return: 总收益率
   - sharpe_ratio: 夏普比率
   - max_drawdown: 最大回撤
   - win_rate: 胜率
   - total_trades: 总交易次数
5. 保存回测结果
```

### 📤 输出

**回测结果**:
```python
{
    'metrics': {
        'total_return': 15.5,       # %
        'sharpe_ratio': 1.8,
        'max_drawdown': -8.2,       # %
        'win_rate': 62.5,           # %
        'total_trades': 100,
        'avg_trade_duration': '2h 30m',
        'profit_factor': 1.85
    },
    'trades': [
        {
            'entry_time': '2025-12-01 10:00:00',
            'exit_time': '2025-12-01 11:00:00',
            'action': 'buy',
            'entry_price': 49500.0,
            'exit_price': 50000.0,
            'quantity': 0.002,
            'profit': 50.0,
            'profit_pct': 1.01,
            'duration': '1h'
        },
        ...
    ]
}
```

**归档文件**:
```
data/step8/20251217/
├── step8_backtest_BTCUSDT_5m_20251201_20251217_v1.json
├── step8_performance_BTCUSDT_5m_20251201_20251217_v1.txt
├── step8_trades_BTCUSDT_5m_20251201_20251217_v1.csv
└── step8_trades_BTCUSDT_5m_20251201_20251217_v1.parquet
```

---

## Step 9: 实时交易事件归档

### 📥 输入
```python
{
    'trade_event': {
        'trade_id': 'ORD_20251217_001',
        'timestamp': '2025-12-17T23:35:15',
        'signal': 'SELL',
        'price': 89782.0,
        'quantity': 0.001,
        'amount': 111.45,
        'order_id': 'ORD_20251217_001',
        'success': True,
        'decision': {...},
        'execution_result': {...},
        'market_state_snapshot': {...},
        'account_info': {'available_balance': 139.31}
    },
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'trade_id': 'ORD_20251217_001'
}
```

### ⚙️ 处理逻辑
**位置**: `src/utils/data_saver.py: save_step9_trade_event()`

```python
# 第957-1014行

1. 保存单笔交易详情 (JSON):
   json_file = 'step9_trade_{symbol}_{timeframe}_{timestamp}_{trade_id}.json'
   with open(json_file, 'w') as f:
       json.dump(trade_event, f, indent=2)

2. 追加到当日 CSV 汇总:
   csv_file = 'step9_trades_{symbol}_{timeframe}_{YYYYMMDD}.csv'
   df_event = pd.DataFrame([trade_event])
   if exists(csv_file):
       df_combined = pd.concat([read_csv(csv_file), df_event])
       df_combined.to_csv(csv_file)
   else:
       df_event.to_csv(csv_file)

3. 追加到当日 Parquet 汇总:
   parquet_file = 'step9_trades_{symbol}_{timeframe}_{YYYYMMDD}.parquet'
   df_combined.to_parquet(parquet_file)

4. 生成/更新每日摘要报告:
   - 读取当日所有交易
   - 统计交易次数、金额、成功率
   - 计算平均价格、最高/最低价
   - 列出最近5笔交易
```

### 📤 输出

**单笔交易 JSON**:
```python
{
    'trade_id': 'ORD_20251217_001',
    'timestamp': '2025-12-17T23:35:15.123456',
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'signal': 'SELL',
    'price': 89782.0,
    'quantity': 0.001,
    'amount': 111.45,
    'order_id': 'ORD_20251217_001',
    'success': True,
    'leverage': 1,
    'stop_loss': 88884.18,
    'take_profit': 91577.64,
    'decision': {
        'action': 'open_short',
        'position_size_pct': 80,
        'leverage': 1,
        'take_profit_pct': 2,
        'stop_loss_pct': 1
    },
    'execution_result': {
        'success': True,
        'order_id': 'ORD_20251217_001',
        'status': 'filled',
        'filled_price': 89782.0,
        'filled_quantity': 0.001,
        'fee': 0.11
    },
    'market_state_snapshot': {
        'current_price': 89782.0,
        'timeframes': {
            '5m': {'rsi': 71.6, 'trend': 'uptrend'},
            '15m': {'rsi': 75.5, 'trend': 'uptrend'},
            '1h': {'rsi': 73.1, 'trend': 'uptrend'}
        }
    },
    'account_info': {
        'available_balance': 139.31
    }
}
```

**归档文件**:
```
data/step9/20251217/
├── step9_trade_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json  (单笔详情)
├── step9_trades_BTCUSDT_5m_20251217.csv                          (当日汇总CSV)
├── step9_trades_BTCUSDT_5m_20251217.parquet                      (当日汇总Parquet)
└── live_trades_daily_summary_BTCUSDT_5m.txt                      (每日摘要)
```

**每日摘要示例**:
```
================================================================================
实时交易每日摘要报告
================================================================================

交易对: BTCUSDT
时间周期: 5m
报告日期: 2025-12-17
最后更新: 2025-12-17 23:35:20

交易统计:
  总交易次数: 3
  买入信号: 1 次
  卖出信号: 2 次
  持有信号: 0 次
  成功执行: 3 次
  失败次数: 0 次

金额统计:
  总交易金额: $334.35
  平均交易金额: $111.45
  最大交易金额: $115.20
  最小交易金额: $108.70

价格统计:
  平均价格: $89,650.00
  最高价格: $89,920.00
  最低价格: $89,250.00

最近5笔交易:
  2025-12-17 23:35:15: SELL @ $89,782.00 × 0.001000 = $111.45
  2025-12-17 22:18:30: SELL @ $89,920.00 × 0.001280 = $115.20
  2025-12-17 21:05:12: BUY  @ $89,250.00 × 0.001218 = $108.70
```

---

## 📊 数据流转总结

### 完整流程概览

```
输入 → 处理 → 输出 → 下一步输入

Step 0: 配置 → 初始化 → Bot实例 → ✓
Step 1: API请求 → 获取K线 → OHLCV数据 → Step 2
Step 2: OHLCV → 计算指标 → 技术指标DF → Step 3
Step 3: 指标DF → 提取特征 → 特征DF → Step 4
Step 4: 多周期特征 → 构建上下文 → 市场上下文 → Step 5
Step 5: 市场上下文 → 格式化 → Markdown文本 → Step 6
Step 6: 市场上下文 → 决策逻辑 → 交易信号 → Step 7
Step 7: 信号+上下文 → 执行交易 → 订单结果 → Step 9
Step 8: 历史数据 → 回测模拟 → 绩效报告 → (离线)
Step 9: 交易事件 → 归档保存 → 多格式文件 → (完成)
```

### 关键数据转换

| 转换阶段 | 输入格式 | 输出格式 | 数据量变化 |
|----------|----------|----------|------------|
| Step 0→1 | 配置 | K线列表 | 0 → 100行 |
| Step 1→2 | K线列表 | DataFrame | 100行×11列 → 100行×31列 |
| Step 2→3 | 指标DF | 特征DF | 100行×31列 → 100行×25列 |
| Step 3→4 | 特征DF | 上下文JSON | 100行 → 1个对象 |
| Step 4→5 | 上下文 | Markdown | 1个对象 → 文本 |
| Step 5→6 | 上下文 | 决策 | 多周期数据 → 单一信号 |
| Step 6→7 | 决策 | 订单 | 信号 → 执行结果 |
| Step 7→9 | 订单 | 归档 | 1笔 → 多格式存储 |

### 数据质量保证

| 步骤 | 质量检查 | 处理方式 |
|------|----------|----------|
| Step 1 | 时间戳连续性 | 自动排序 |
| Step 2 | 异常值检测 | MAD + Clip |
| Step 2 | 预热期标记 | is_warmup=True |
| Step 3 | 特征有效性 | is_feature_valid |
| Step 3 | 时间缺口 | has_time_gap |
| Step 7 | 最小名义 | MIN_NOTIONAL检查 |

---

📅 **最后更新**: 2025-12-17  
✍️ **作者**: AI Trader Team  
🔄 **版本**: v2.1 (输入→处理→输出格式)
