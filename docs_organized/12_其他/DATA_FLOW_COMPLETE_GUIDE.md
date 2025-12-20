# AI 量化交易系统完整数据流转指南

## 📊 概述

本文档详细描述 AI 量化交易系统从原始数据获取到交易执行的完整数据流转过程，包括每个步骤的处理逻辑、输入输出和数据结构。

---

## 🔄 完整数据流转架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI 量化交易系统数据流                          │
└─────────────────────────────────────────────────────────────────┘

Step 0: 实盘交易启动
   ↓
Step 1: 获取原始K线数据 (get_klines)
   ↓ [原始 OHLCV 数据]
   data/step1/YYYYMMDD/*.{json,csv,parquet,txt}
   ↓
Step 2: 计算技术指标 (process_klines)
   ↓ [OHLCV + 技术指标]
   data/step2/YYYYMMDD/*.{parquet,txt}
   ↓
Step 3: 提取特征快照 (build_features)
   ↓ [归一化特征]
   data/step3/YYYYMMDD/*.{parquet,txt}
   ↓
Step 4: 构建多周期上下文 (build_market_context)
   ↓ [5m/15m/1h 综合分析]
   data/step4/YYYYMMDD/*.json
   ↓
Step 5: 格式化 Markdown 文本 (format_to_markdown)
   ↓ [LLM 输入文本]
   data/step5/YYYYMMDD/*.{md,txt}
   ↓
Step 6: 生成交易决策 (generate_signal)
   ↓ [BUY/SELL/HOLD]
   data/step6/YYYYMMDD/*.{json,txt}
   ↓
Step 7: 执行交易 (execute_trade) [可选]
   ↓ [订单执行记录]
   data/step7/YYYYMMDD/*.{json,csv}
   ↓
Step 8: 回测分析 (run_backtest) [可选]
   ↓ [绩效评估]
   data/step8/YYYYMMDD/*.{json,parquet,csv,txt}
   ↓
Step 9: 实时交易事件归档 (save_step9_trade_event) [可选]
   ↓ [每笔交易记录]
   data/step9/YYYYMMDD/*.{json,csv,parquet}
```

---

## 📝 各步骤详细说明

### Step 0: 实盘交易启动

**位置**: `run_live_trading.py`

**函数**: `LiveTradingBot.__init__()` → `run_once()`

**输入**:
- 配置参数 (TRADING_CONFIG)
- API 密钥 (环境变量)

**处理逻辑**:
1. 初始化 Binance 客户端
2. 初始化数据处理器、特征构建器、风险管理器
3. 实例化 DataSaver
4. 获取账户余额

**输出**:
- 初始化完成的交易机器人实例
- 账户余额信息

**关键代码**:
```python
# run_live_trading.py: 68-90
def __init__(self, config: Dict = None):
    self.config_dict = config or TRADING_CONFIG.copy()
    self.client = BinanceClient()
    self.processor = MarketDataProcessor()
    self.feature_builder = FeatureBuilder()
    self.risk_manager = RiskManager()
    self.execution_engine = ExecutionEngine(...)
    self.data_saver = DataSaver()  # 实例化数据保存器
```

---

### Step 1: 获取原始K线数据

**位置**: `src/api/binance_client.py`

**函数**: `BinanceClient.get_klines()`

**输入**:
```python
{
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'limit': 100
}
```

**处理逻辑**:
1. 调用 Binance API 获取 K线数据
2. 转换时间戳为毫秒
3. 格式化为标准字典结构
4. 保存到 step1

**输出 (每根K线)**:
```python
{
    'timestamp': 1734451500000,          # Unix 时间戳 (毫秒)
    'open': 89500.0,                     # 开盘价
    'high': 89600.0,                     # 最高价
    'low': 89400.0,                      # 最低价
    'close': 89550.0,                    # 收盘价
    'volume': 42.5,                      # 成交量 (BTC)
    'close_time': 1734451799999,         # 收盘时间
    'quote_volume': 3806875.0,           # 成交额 (USDT)
    'trades': 850,                       # 成交笔数
    'taker_buy_volume': 21.3,            # 主动买入量
    'taker_buy_quote_volume': 1903438.0  # 主动买入额
}
```

**归档文件**:
```
data/step1/20251217/
├── step1_klines_BTCUSDT_5m_20251217_233509.json     # 完整 JSON (含元数据)
├── step1_klines_BTCUSDT_5m_20251217_233509.csv      # CSV 格式
├── step1_klines_BTCUSDT_5m_20251217_233509.parquet  # Parquet 格式
└── step1_stats_BTCUSDT_5m_20251217_233509.txt       # 统计报告
```

**关键代码**:
```python
# run_live_trading.py: 119-125
klines_5m = self.client.get_klines(symbol, '5m', limit=100)
klines_15m = self.client.get_klines(symbol, '15m', limit=100)
klines_1h = self.client.get_klines(symbol, '1h', limit=100)

# 保存到 step1
self.data_saver.save_step1_klines(klines_5m, symbol, '5m')
```

---

### Step 2: 计算技术指标

**位置**: `src/data/processor.py`

**函数**: `MarketDataProcessor.process_klines()`

**输入**:
- Step1 的 K线数据列表 (100根)
- symbol: 'BTCUSDT'
- timeframe: '5m'

**处理逻辑**:

#### 2.1 数据验证 (DataValidator)
```python
# src/data/validator.py: validate_and_clean_klines()
1. 异常值检测 (MAD 方法，阈值=5.0)
2. 异常值处理 (clip 到邻域中位数)
3. 生成验证报告
```

#### 2.2 转换为 DataFrame
```python
# src/data/processor.py: 42-60
df = pd.DataFrame(klines)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df = df.set_index('timestamp')
```

#### 2.3 计算技术指标
```python
# src/data/processor.py: _calculate_indicators()
以下指标按顺序计算：

1. SMA (简单移动平均)
   - sma_20 = close.rolling(20).mean()
   - sma_50 = close.rolling(50).mean()

2. EMA (指数移动平均)
   - ema_12 = close.ewm(span=12).mean()
   - ema_26 = close.ewm(span=26).mean()

3. MACD (移动平均收敛发散)
   - macd = (ema_12 - ema_26) / close * 100  # 归一化
   - macd_signal = macd.ewm(span=9).mean()
   - macd_hist = macd - macd_signal
   - macd_diff = macd_hist  # 别名

4. RSI (相对强弱指数)
   - rsi = ta.momentum.RSIIndicator(close, 14).rsi()

5. 布林带 (Bollinger Bands)
   - bb_middle = sma_20
   - bb_std = close.rolling(20).std()
   - bb_upper = bb_middle + 2 * bb_std
   - bb_lower = bb_middle - 2 * bb_std
   - bb_width = (bb_upper - bb_lower) / bb_middle * 100

6. ATR (平均真实波幅)
   - true_range = max(high-low, abs(high-prev_close), abs(low-prev_close))
   - atr = true_range.ewm(span=14).mean()
   - atr_pct = atr / close * 100

7. 成交量指标
   - volume_sma = volume.rolling(20).mean()
   - volume_ratio = volume / volume_sma

8. VWAP (成交量加权平均价)
   - price_volume = (high + low + close) / 3 * volume
   - vwap = price_volume.rolling(20).sum() / volume.rolling(20).sum()

9. OBV (能量潮)
   - obv = cumsum(volume * sign(close.diff()))

10. 价格变化
    - price_change_pct = close.pct_change() * 100
    - high_low_range = (high - low) / close * 100
```

#### 2.4 标记预热期
```python
# src/data/processor.py: _mark_warmup_period()
- 前 50 根K线标记为 is_warmup=True
- 前 50 根K线标记为 is_valid=False
```

#### 2.5 生成快照
```python
# src/data/processor.py: 108-138
snapshot_id = hashlib.md5(...)[:8]
last_row = df.iloc[-1]
snapshot_data = {
    'snapshot_id': snapshot_id,
    'timestamp': last_row.name,
    'close': last_row['close'],
    'volume': last_row['volume'],
    ...
}
```

**输出 DataFrame 列 (31列)**:
```
基础列 (10):
- timestamp, open, high, low, close, volume, close_time, 
  quote_volume, trades, taker_buy_volume, taker_buy_quote_volume

技术指标 (21):
- sma_20, sma_50, ema_12, ema_26
- macd, macd_signal, macd_hist, macd_diff
- rsi
- bb_upper, bb_middle, bb_lower, bb_width
- atr, atr_pct, true_range
- volume_sma, volume_ratio
- vwap, obv
- price_change_pct, high_low_range
- is_warmup, is_valid
```

**归档文件**:
```
data/step2/20251217/
├── step2_indicators_BTCUSDT_5m_20251217_233509_<snapshot_id>.parquet  # 完整指标数据
└── step2_stats_BTCUSDT_5m_20251217_233509_<snapshot_id>.txt           # 统计报告
```

**关键代码**:
```python
# run_live_trading.py: 127-135
df_5m = self.processor.process_klines(klines_5m, symbol, '5m')
df_15m = self.processor.process_klines(klines_15m, symbol, '15m')
df_1h = self.processor.process_klines(klines_1h, symbol, '1h')

# 保存到 step2
self.data_saver.save_step2_indicators(df_5m, symbol, '5m', snapshot_id='unknown')
```

---

### Step 3: 提取特征快照

**位置**: `src/features/builder.py`

**函数**: `FeatureBuilder.build_features()`

**输入**:
- Step2 的 DataFrame (含技术指标)

**处理逻辑**:

#### 3.1 特征提取
```python
# src/features/builder.py: 20-80
提取以下特征组：

1. 价格特征 (4)
   - price_change_pct
   - high_low_range
   - close_to_sma20_ratio = (close - sma_20) / sma_20 * 100
   - close_to_ema12_ratio = (close - ema_12) / ema_12 * 100

2. 趋势特征 (6)
   - macd, macd_signal, macd_hist
   - ema_12, ema_26
   - sma_20

3. 动量特征 (1)
   - rsi

4. 波动率特征 (5)
   - bb_upper, bb_middle, bb_lower, bb_width
   - atr_pct

5. 成交量特征 (3)
   - volume_ratio
   - obv
   - vwap

6. 布林带位置 (1)
   - bb_position = (close - bb_lower) / (bb_upper - bb_lower) * 100
```

#### 3.2 特征归一化
```python
# src/features/builder.py: 82-120
对以下特征进行归一化（除以当前价格）：
- ema_12, ema_26, sma_20
- bb_upper, bb_middle, bb_lower
- vwap

百分比特征保持不变：
- rsi, macd, bb_width, atr_pct, volume_ratio
```

#### 3.3 数据质量标记
```python
# src/features/builder.py: 122-145
- is_feature_valid: 检查所有特征是否有效（非 NaN/Inf）
- has_time_gap: 检查时间间隔是否异常
- is_warmup: 复制自 step2
```

**输出 DataFrame 列 (约 25列)**:
```
特征列：
- price_change_pct, high_low_range
- close_to_sma20_ratio, close_to_ema12_ratio
- macd, macd_signal, macd_hist
- ema_12_norm, ema_26_norm, sma_20_norm
- rsi
- bb_upper_norm, bb_middle_norm, bb_lower_norm, bb_width, bb_position
- atr_pct
- volume_ratio, obv, vwap_norm

质量标记：
- is_feature_valid, has_time_gap, is_warmup
```

**归档文件**:
```
data/step3/20251217/
├── step3_features_BTCUSDT_5m_20251217_233509_v1.parquet  # 特征数据
└── step3_stats_BTCUSDT_5m_20251217_233509_v1.txt         # 统计报告
```

**关键代码**:
```python
# run_live_trading.py: 137-143
features_5m = self.feature_builder.build_features(df_5m)
features_15m = self.feature_builder.build_features(df_15m)
features_1h = self.feature_builder.build_features(df_1h)

# 保存到 step3
self.data_saver.save_step3_features(features_5m, symbol, '5m', 
                                    source_snapshot_id='unknown', feature_version='v1')
```

---

### Step 4: 构建多周期上下文

**位置**: `src/features/builder.py`

**函数**: `FeatureBuilder.build_market_context()`

**输入**:
```python
{
    'symbol': 'BTCUSDT',
    'multi_timeframe_states': {
        '5m': {...},   # Step 3 的最后一行特征
        '15m': {...},  # Step 3 的最后一行特征
        '1h': {...}    # Step 3 的最后一行特征
    },
    'snapshot': {...},         # 当前市场快照
    'position_info': None      # 持仓信息（可选）
}
```

**处理逻辑**:
```python
# src/features/builder.py: 150-200
1. 提取各周期的关键指标：
   - price, rsi, macd, macd_signal, trend

2. 判断趋势方向：
   - uptrend: sma_20 > sma_50 且 price > sma_20
   - downtrend: sma_20 < sma_50 且 price < sma_20
   - sideways: 其他

3. 构建综合市场上下文
```

**输出结构**:
```python
{
    'symbol': 'BTCUSDT',
    'current_price': 89782.0,
    'timeframes': {
        '5m': {
            'price': 89782.0,
            'rsi': 71.60,
            'macd': 0.15,
            'macd_signal': 0.13,
            'trend': 'uptrend'
        },
        '15m': {...},
        '1h': {...}
    },
    'snapshot': {
        'price': {...},
        'funding': {...},
        'oi': {},
        'orderbook': {}
    },
    'position_info': None
}
```

**归档文件**:
```
data/step4/20251217/
└── step4_context_BTCUSDT_5m_20251217_233510_unknown.json  # 上下文JSON
```

**关键代码**:
```python
# run_live_trading.py: 145-152
# 提取关键指标
multi_timeframe_states = {
    '5m': self._extract_key_indicators(df_5m),
    '15m': self._extract_key_indicators(df_15m),
    '1h': self._extract_key_indicators(df_1h)
}

# 构建市场上下文
market_state = self.feature_builder.build_market_context(
    symbol=symbol,
    multi_timeframe_states=multi_timeframe_states,
    snapshot=snapshot,
    position_info=None
)

# 保存到 step4
self.data_saver.save_step4_context(market_state, symbol, '5m', snapshot_id='unknown')
```

---

### Step 5: 格式化 Markdown 文本

**位置**: `run_live_trading.py`

**函数**: (内联逻辑)

**输入**:
- Step 4 的市场上下文

**处理逻辑**:
```python
# run_live_trading.py: 154-176
1. 提取各周期的趋势和 RSI
2. 统计上涨/下跌周期数
3. 生成交易信号
4. 格式化为 Markdown 文本
```

**输出 Markdown**:
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
├── step5_llm_input_BTCUSDT_5m_20251217_233510_live.md   # Markdown 文本
└── step5_stats_BTCUSDT_5m_20251217_233510_live.txt      # 统计报告
```

**关键代码**:
```python
# run_live_trading.py: 154-176
timeframes = market_state.get('timeframes', {})
trend_5m = timeframes.get('5m', {}).get('trend', 'unknown')
rsi_5m = timeframes.get('5m', {}).get('rsi', 50)
# ... (提取其他周期)

markdown_text = f"""# 市场分析报告
            
## 交易对信息
- **交易对**: {symbol}
- **当前价格**: ${current_price:,.2f}
...
"""

# 保存到 step5
self.data_saver.save_step5_markdown(markdown_text, symbol, '5m', snapshot_id='live')
```

---

### Step 6: 生成交易决策

**位置**: `run_live_trading.py`

**函数**: `LiveTradingBot.generate_signal()`

**输入**:
- Step 4 的市场上下文

**处理逻辑**:
```python
# run_live_trading.py: 208-234
决策规则：

1. 买入信号 (BUY)：
   - 至少2个周期上涨
   - AND rsi_1h < 70
   - AND rsi_15m < 75

2. 卖出信号 (SELL)：
   - 至少2个周期下跌
   - OR (rsi_5m > 80 AND rsi_15m > 75)

3. 观望信号 (HOLD)：
   - 其他情况
```

**输出结构**:
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
    'timestamp': '2025-12-17T23:35:10.134048'
}
```

**归档文件**:
```
data/step6/20251217/
├── step6_decision_BTCUSDT_5m_20251217_233510_live.json  # 决策JSON
└── step6_stats_BTCUSDT_5m_20251217_233510_live.txt      # 统计报告
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
    
    # 决策逻辑
    if uptrend_count >= 2 and rsi_1h < 70 and rsi_15m < 75:
        return 'BUY'
    
    if downtrend_count >= 2 or (rsi_5m > 80 and rsi_15m > 75):
        return 'SELL'
    
    return 'HOLD'

# 保存决策
decision_data = {
    'signal': signal,
    'confidence': 0,
    'analysis': {...},
    'timestamp': datetime.now().isoformat()
}
self.data_saver.save_step6_decision(decision_data, symbol, '5m', snapshot_id='live')
```

---

### Step 7: 执行交易 (可选 - 仅当信号为 BUY/SELL)

**位置**: `run_live_trading.py`

**函数**: `LiveTradingBot.execute_trade()`

**输入**:
```python
{
    'signal': 'SELL',
    'market_state': {...}
}
```

**处理逻辑**:

#### 7.1 前置检查
```python
# run_live_trading.py: 251-265
1. 检查信号 (跳过 HOLD)
2. 获取当前价格
3. 计算交易金额
4. 检查最小名义金额（✅ 动态获取，不同交易对不同，通常 5-10 USDT）
5. 计算交易数量
```

#### 7.2 用户确认
```python
# run_live_trading.py: 267-281
1. 显示交易信息
2. 等待确认（5秒，可配置）
3. 支持 Ctrl+C 取消
```

#### 7.3 构建决策
```python
# run_live_trading.py: 283-309
decision = {
    'action': 'open_long' / 'open_short',
    'symbol': 'BTCUSDT',
    'position_size_pct': 80,
    'leverage': 1,
    'take_profit_pct': 2,
    'stop_loss_pct': 1
}
```

#### 7.4 执行订单
```python
# run_live_trading.py: 311-326
result = self.execution_engine.execute_decision(
    decision=decision,
    account_info={'available_balance': balance},
    position_info=None,
    current_price=current_price
)
```

#### 7.5 记录交易
```python
# run_live_trading.py: 328-369
1. 使用 trade_logger 记录开仓
2. 保存到交易历史
3. 归档到 step9 (新增)
```

**输出结构**:
```python
{
    'order_id': 'ORD_20251217_001',
    'symbol': 'BTCUSDT',
    'action': 'open_short',
    'quantity': 0.001,
    'price': 89782.0,
    'total_value': 111.45,
    'fee': 0.11,
    'status': 'filled',
    'filled_time': '2025-12-17T23:35:15',
    'leverage': 1,
    'stop_loss': 88884.18,
    'take_profit': 91577.64
}
```

**归档文件**:
```
data/step7/20251217/
├── step7_execution_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json  # 单笔JSON
└── step7_executions_BTCUSDT_5m.csv                                    # 汇总CSV
```

**关键代码**:
```python
# run_live_trading.py: 236-369
def execute_trade(self, signal: str, market_state: Dict) -> bool:
    if signal == 'HOLD':
        return False
    
    try:
        # 获取当前价格
        current_price = market_state.get('current_price', 0)
        
        # 计算交易数量
        balance = self.get_account_balance()
        trade_amount = min(self.max_position_size, 
                          balance * (self.config_dict['position_pct'] / 100))
        
        # 检查最小名义金额（✅ 动态获取）
        # Binance 合约不同交易对要求不同（通常 5-10 USDT）
        MIN_NOTIONAL = self.client.get_symbol_min_notional(symbol)
        if MIN_NOTIONAL == 0:
            MIN_NOTIONAL = 5.0  # 无法获取时使用保守默认值
        
        # 检查名义价值（保证金 × 杠杆）
        notional_value = trade_amount * self.config_dict['leverage']
        if notional_value < MIN_NOTIONAL:
            print(f"\n⚠️  名义价值 ${notional_value:.2f} 低于最低要求 ${MIN_NOTIONAL:.2f}")
            return False
        
        quantity = trade_amount / current_price
        
        # 用户确认
        if self.config_dict['confirm_before_trade']:
            print(f"\n⚠️  即将执行真实交易！")
            time.sleep(self.config_dict['confirm_seconds'])
        
        # 执行交易
        if signal == 'BUY':
            decision = {'action': 'open_long', ...}
        else:
            decision = {'action': 'open_short', ...}
        
        result = self.execution_engine.execute_decision(...)
        
        if result and result.get('success'):
            # 记录交易
            trade_logger.log_open_position(...)
            self.trade_history.append(...)
            
            # 归档到 step9 (新增)
            trade_event = {...}
            self.data_saver.save_step9_trade_event(trade_event, symbol, timeframe)
            
            return True
    except Exception as e:
        print(f"\n❌ 交易执行错误: {e}")
        return False
```

---

### Step 8: 回测分析 (可选 - 仅在回测模式)

**位置**: (未在实盘使用，仅用于历史数据回测)

**输入**:
```python
{
    'symbol': 'BTCUSDT',
    'timeframe': '5m',
    'start_date': '20251201',
    'end_date': '20251217',
    'strategy_version': 'v1'
}
```

**处理逻辑**:
1. 加载历史数据
2. 模拟交易执行
3. 计算绩效指标
4. 生成回测报告

**输出结构**:
```python
{
    'metrics': {
        'total_return': 15.5,
        'sharpe_ratio': 1.8,
        'max_drawdown': -8.2,
        'win_rate': 62.5,
        'total_trades': 100
    },
    'trades': [
        {
            'entry_time': '2025-12-01 10:00:00',
            'exit_time': '2025-12-01 11:00:00',
            'action': 'buy',
            'entry_price': 49500.0,
            'exit_price': 50000.0,
            'profit': 50.0
        },
        ...
    ]
}
```

**归档文件**:
```
data/step8/20251217/
├── step8_backtest_BTCUSDT_5m_20251201_20251217_v1.json       # 回测结果
├── step8_performance_BTCUSDT_5m_20251201_20251217_v1.txt     # 绩效报告
├── step8_trades_BTCUSDT_5m_20251201_20251217_v1.csv          # 交易CSV
└── step8_trades_BTCUSDT_5m_20251201_20251217_v1.parquet      # 交易Parquet
```

---

### Step 9: 实时交易事件归档 (可选 - 仅当执行交易)

**位置**: `src/utils/data_saver.py`

**函数**: `DataSaver.save_step9_trade_event()`

**输入**:
```python
{
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
}
```

**处理逻辑**:
```python
# src/utils/data_saver.py: 957-1014
1. 保存单笔交易详情为 JSON
2. 追加到当日 CSV 汇总
3. 追加到当日 Parquet 汇总
4. 生成每日摘要报告
```

**输出结构** (单笔 JSON):
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
        ...
    },
    'execution_result': {
        'order_id': 'ORD_20251217_001',
        'status': 'filled',
        ...
    },
    'market_state_snapshot': {
        'current_price': 89782.0,
        'timeframes': {
            '5m': {'rsi': 71.6, 'trend': 'uptrend'},
            ...
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
├── step9_trade_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json  # 单笔详情
├── step9_trades_BTCUSDT_5m_20251217.csv                          # 当日汇总CSV
├── step9_trades_BTCUSDT_5m_20251217.parquet                      # 当日汇总Parquet
└── live_trades_daily_summary_BTCUSDT_5m.txt                      # 每日摘要
```

**关键代码**:
```python
# run_live_trading.py: 345-369
# 同步归档到 step9：实时交易事件
try:
    symbol = market_state.get('symbol', 'BTCUSDT')
    timeframe = market_state.get('timeframe', '5m')
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
except Exception as e:
    print(f"⚠️ step9 交易归档失败: {e}")
```

---

## 📊 数据结构对比表

| 步骤 | 数据量 | 列数 | 主要格式 | 关键字段 |
|------|--------|------|----------|----------|
| Step1 | 100行 | 11列 | JSON/CSV/Parquet | timestamp, open, high, low, close, volume |
| Step2 | 100行 | 31列 | Parquet | +20个技术指标 (rsi, macd, bb, atr...) |
| Step3 | 100行 | 25列 | Parquet | 归一化特征 + 质量标记 |
| Step4 | 1个 | - | JSON | 多周期上下文 (3个时间框架) |
| Step5 | 1个 | - | Markdown | 市场分析报告文本 |
| Step6 | 1个 | - | JSON | 交易信号 + 分析 |
| Step7 | 1笔 | - | JSON+CSV | 订单执行记录 |
| Step8 | 多笔 | - | JSON+Parquet | 回测绩效 + 交易历史 |
| Step9 | 1笔 | - | JSON+CSV+Parquet | 实时交易事件 |

---

## 🔧 关键函数调用链

### 实盘交易完整流程

```python
# run_live_trading.py: main() → LiveTradingBot.run_once()

1. get_account_balance()
   └─> BinanceClient.get_futures_account()

2. get_market_data()
   ├─> BinanceClient.get_klines() × 3 (5m/15m/1h)
   │   └─> DataSaver.save_step1_klines() × 3
   │
   ├─> MarketDataProcessor.process_klines() × 3
   │   ├─> DataValidator.validate_and_clean_klines()
   │   ├─> _calculate_indicators()
   │   └─> _mark_warmup_period()
   │   └─> DataSaver.save_step2_indicators() × 3
   │
   ├─> FeatureBuilder.build_features() × 3
   │   └─> DataSaver.save_step3_features() × 3
   │
   ├─> FeatureBuilder.build_market_context()
   │   └─> DataSaver.save_step4_context()
   │
   └─> (format markdown)
       └─> DataSaver.save_step5_markdown()

3. generate_signal()
   └─> DataSaver.save_step6_decision()

4. execute_trade() [if signal != HOLD]
   ├─> ExecutionEngine.execute_decision()
   │   └─> BinanceClient.place_market_order()
   │
   ├─> trade_logger.log_open_position()
   └─> DataSaver.save_step9_trade_event()
```

---

## 📁 文件命名规范

### 命名模式

```
stepX_<type>_<symbol>_<timeframe>_<timestamp>_<id>.<ext>

示例:
- step1_klines_BTCUSDT_5m_20251217_233509.json
- step2_indicators_BTCUSDT_5m_20251217_233509_unknown.parquet
- step3_features_BTCUSDT_5m_20251217_233509_v1.parquet
- step4_context_BTCUSDT_5m_20251217_233510_unknown.json
- step5_llm_input_BTCUSDT_5m_20251217_233510_live.md
- step6_decision_BTCUSDT_5m_20251217_233510_live.json
- step7_execution_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json
- step9_trade_BTCUSDT_5m_20251217_235515_ORD_20251217_001.json
```

### 时间戳格式

- 文件名: `YYYYMMDD_HHMMSS` (本地时间)
- 数据内容: Unix 毫秒时间戳 或 ISO 8601 格式

---

## 🔍 数据验证与质量保证

### Step1-2: 数据验证
```python
# src/data/validator.py
- MAD 异常检测 (阈值=5.0)
- Clip 异常值到邻域中位数
- 记录验证报告
```

### Step2: 预热期标记
```python
# 前 50 根K线标记为不可用
is_warmup = True (index < 50)
is_valid = False (index < 50)
```

### Step3: 特征质量
```python
# 检查所有特征是否有效
is_feature_valid = not (has_nan or has_inf)
has_time_gap = (time_diff > expected * 1.5)
```

---

## 📈 实际运行示例

### 输入 (API 请求)
```
GET /fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=100
```

### 输出 (归档文件)
```
data/
├── step1/20251217/
│   ├── step1_klines_BTCUSDT_5m_20251217_233509.json     (33.4 KB)
│   ├── step1_klines_BTCUSDT_5m_20251217_233509.csv      (13.6 KB)
│   ├── step1_klines_BTCUSDT_5m_20251217_233509.parquet  (17.3 KB)
│   └── step1_stats_BTCUSDT_5m_20251217_233509.txt       (2.1 KB)
│
├── step2/20251217/
│   ├── step2_indicators_BTCUSDT_5m_20251217_233509_unknown.parquet  (28.5 KB)
│   └── step2_stats_BTCUSDT_5m_20251217_233509_unknown.txt           (3.8 KB)
│
├── step3/20251217/
│   ├── step3_features_BTCUSDT_5m_20251217_233509_v1.parquet  (22.1 KB)
│   └── step3_stats_BTCUSDT_5m_20251217_233509_v1.txt         (4.2 KB)
│
├── step4/20251217/
│   └── step4_context_BTCUSDT_5m_20251217_233510_unknown.json  (1.5 KB)
│
├── step5/20251217/
│   ├── step5_llm_input_BTCUSDT_5m_20251217_233510_live.md    (0.8 KB)
│   └── step5_stats_BTCUSDT_5m_20251217_233510_live.txt       (0.5 KB)
│
└── step6/20251217/
    ├── step6_decision_BTCUSDT_5m_20251217_233510_live.json  (0.6 KB)
    └── step6_stats_BTCUSDT_5m_20251217_233510_live.txt      (0.4 KB)

(如果有交易信号，还会生成 step7 和 step9)
```

---

## 🎯 总结

### 数据流转特点

1. **层次化处理**: 从原始数据 → 技术指标 → 特征 → 上下文 → 决策
2. **多格式支持**: JSON (易读) + CSV (兼容) + Parquet (高效)
3. **质量保证**: 每步都有验证、清洗、标记
4. **完整追溯**: 所有中间结果都归档，可重现
5. **时间同步**: 使用一致的时间戳和 snapshot_id

### 关键改进点

1. ✅ **最小名义金额检查** (Step7)
2. ✅ **MACD 归一化** (Step2)
3. ✅ **ATR 前期0值修复** (Step2)
4. ✅ **VWAP 滚动窗口** (Step2)
5. ✅ **Step9 实时交易归档** (新增)

### 下一步优化建议

1. **Step2**: 添加更多技术指标 (KDJ, CCI, Williams %R)
2. **Step3**: 机器学习特征工程 (PCA, 特征选择)
3. **Step6**: 集成真实 LLM 模型 (GPT-4, Claude)
4. **Step7**: 风险管理增强 (动态仓位、止损优化)
5. **Step8**: 完整回测框架 (vectorbt, backtrader)

---

## 📚 相关文档

- [DataSaver 完整功能指南](DATA_SAVER_FULL_GUIDE.md)
- [技术指标计算说明](INDICATOR_CALCULATION_GUIDE.md)
- [实盘交易配置](run_live_trading.py)
- [数据保存器源码](src/utils/data_saver.py)
- [数据处理器源码](src/data/processor.py)
- [特征构建器源码](src/features/builder.py)

---

📅 最后更新: 2025-12-17  
✍️ 作者: AI Trader Team  
🔄 版本: v2.0 (支持 Step 1-9 完整流转)
