# 🔴 数据质量与决策一致性问题

## 📋 问题陈述

**核心矛盾：趋势判断是"硬规则"，但数据来自"软处理"**

```python
# 决策逻辑：刚性规则
if sma_20 > sma_50 and price > sma_20:
    trend = 'uptrend'
```

**但数据质量存在隐患：**
1. ~~SMA 来自被 MAD 裁剪的数据~~ ✅ **已修复**（废弃MAD裁剪）
2. ~~EMA warmup 不充分~~ ✅ **已修复**（105根warmup期）
3. ⚠️ 多周期未对齐（仍需验证）
4. ⚠️ 数据边界条件未充分测试

---

## ✅ 已修复的问题

### 1. 废弃 MAD 价格裁剪

**问题**：
- 原方案：使用 MAD（中位数绝对偏差）裁剪价格
- 风险：将正常的市场波动误判为异常，扭曲价格数据

**修复**（已完成）：
```python
# src/data/kline_validator.py

# ✅ 新原则：K线是市场事实，绝不修改价格！
# 只检测和处理真正的数据错误：
# 1. 数据完整性问题（缺失字段、NaN、Inf）
# 2. OHLC 逻辑违反（high < low 等）
# 3. 价格超出合理范围（< 0.001 或 > 10M）
# 4. 时间序列问题（重复、断档）

# ❌ 不处理的"异常"（这些都是正常市场行为）：
# - 大幅跳空/涨跌幅
# - 长影线（Pin Bar）
# - MAD 偏离大
# - 连续单边行情
```

**验证状态**：✅ 已通过测试，无价格修改逻辑

---

### 2. Warmup 期修正

**问题**：
- 原方案：50根warmup期
- 风险：MACD 等指标未完全收敛，数值有偏差

**修复**（已完成）：
```python
# src/data/processor.py

# ✅ Warmup 期从 50 提升至 105 根
# 计算依据：
# - EMA12: 3×12 = 36 根收敛
# - EMA26: 3×26 = 78 根收敛
# - MACD Signal: 78 + 3×9 = 105 根完全稳定

WARMUP_PERIOD = 105  # ✅ 从 50 提升至 105

# 标记逻辑：
df['is_warmup'] = True
df['is_valid'] = False

if len(df) > 105:
    df.iloc[105:, df.columns.get_loc('is_warmup')] = False
    df.iloc[105:, df.columns.get_loc('is_valid')] = True
```

**验证状态**：✅ 已通过测试（test_warmup_period_fix.py）

---

## ⚠️ 待验证的问题

### 3. 多周期时间对齐

**问题假设**：
```python
# 理论上，3个周期的"当前时刻"应该对应：
# - 5m:  最后一根完整K线（例如 23:30-23:35）
# - 15m: 最后一根完整K线（例如 23:15-23:30）
# - 1h:  最后一根完整K线（例如 23:00-24:00）

# 问题1：时间戳是否真的对齐？
# 问题2：是否有跨周期的价格一致性检查？
```

**当前实现**：
```python
# run_live_trading.py: _get_timeframe_state()

# ✅ 已使用已完成K线（iloc[-2]）
latest = df.iloc[-2]  # 避免未完成K线

# ⚠️ 但缺少跨周期的时间一致性验证
# 例如：5m 的 23:35 和 15m 的 23:30 是否在合理范围内？
```

**需要的验证**：
1. 检查多周期的时间戳是否在合理范围内
2. 验证价格差异是否在正常波动范围（±0.5%）
3. 记录时间对齐警告（如果存在）

---

### 4. 数据边界条件

**问题假设**：
```python
# 边界条件1：数据量不足
# - 如果 API 返回 < 105 根K线？
# - 如果某个周期缺失数据？

# 边界条件2：指标计算异常
# - 如果 SMA50 全是 NaN？
# - 如果 MACD 出现 Inf？

# 边界条件3：价格数据异常
# - 如果连续多根K线价格完全相同？
# - 如果某周期价格与其他周期偏差 >5%？
```

**当前保护措施**：
```python
# src/data/processor.py

# ✅ 数据量检查
required_bars = max(self.INDICATOR_PARAMS['sma'])  # 50
if len(klines) < required_bars:
    log.error(f"K线数量不足: 需要>={required_bars}, 实际={len(klines)}")
    return pd.DataFrame()

# ✅ NaN 检查（隐式，通过 is_valid 标记）
# 前 105 根标记为 is_valid=False

# ⚠️ 缺少的检查：
# - 指标计算后的 Inf 检查
# - 多周期价格一致性检查
# - SMA/EMA 全为 NaN 的处理
```

---

## 🎯 修复方案

### Phase 1: 数据质量增强检查（推荐立即执行）

#### 1.1 多周期时间对齐验证

```python
# src/features/builder.py: build_market_context()

def _validate_multiframe_alignment(self, multi_timeframe_states: Dict) -> Dict:
    """
    验证多周期时间对齐
    
    Returns:
        {
            'aligned': bool,
            'warnings': List[str],
            'max_time_diff': float  # 秒
        }
    """
    warnings = []
    
    # 提取各周期的时间戳（假设存在）
    timestamps = {}
    for tf, state in multi_timeframe_states.items():
        if 'timestamp' in state:
            timestamps[tf] = state['timestamp']
    
    if len(timestamps) < 2:
        return {'aligned': True, 'warnings': [], 'max_time_diff': 0}
    
    # 计算最大时间差
    ts_values = [pd.Timestamp(t) for t in timestamps.values()]
    max_diff = (max(ts_values) - min(ts_values)).total_seconds()
    
    # 容差：1小时（因为1h周期最慢）
    TOLERANCE_SECONDS = 3600
    
    if max_diff > TOLERANCE_SECONDS:
        warnings.append(
            f"多周期时间差过大: {max_diff:.0f}秒 > {TOLERANCE_SECONDS}秒"
        )
    
    return {
        'aligned': len(warnings) == 0,
        'warnings': warnings,
        'max_time_diff': max_diff
    }
```

#### 1.2 多周期价格一致性验证

```python
# src/features/builder.py: build_market_context()

def _validate_multiframe_prices(self, multi_timeframe_states: Dict) -> Dict:
    """
    验证多周期价格一致性
    
    原则：不同周期的"当前价格"应该在合理范围内（±0.5%）
    
    Returns:
        {
            'consistent': bool,
            'warnings': List[str],
            'price_range': Tuple[float, float]
        }
    """
    warnings = []
    prices = []
    
    # 提取各周期价格
    for tf, state in multi_timeframe_states.items():
        if 'price' in state and state['price'] > 0:
            prices.append((tf, state['price']))
    
    if len(prices) < 2:
        return {'consistent': True, 'warnings': [], 'price_range': (0, 0)}
    
    # 计算价格范围
    price_values = [p for _, p in prices]
    min_price = min(price_values)
    max_price = max(price_values)
    
    # 容差：±0.5%
    TOLERANCE_PCT = 0.5
    price_range_pct = (max_price - min_price) / min_price * 100
    
    if price_range_pct > TOLERANCE_PCT:
        warnings.append(
            f"多周期价格偏差过大: {price_range_pct:.2f}% > {TOLERANCE_PCT}%"
        )
        for tf, price in prices:
            warnings.append(f"  {tf}: {price:.2f}")
    
    return {
        'consistent': len(warnings) == 0,
        'warnings': warnings,
        'price_range': (min_price, max_price),
        'price_range_pct': price_range_pct
    }
```

#### 1.3 指标完整性验证

```python
# src/data/processor.py: process_klines()

def _validate_indicators(self, df: pd.DataFrame, symbol: str) -> Dict:
    """
    验证技术指标完整性
    
    检查项：
    1. 关键指标是否全为 NaN
    2. 是否存在 Inf 值
    3. 有效数据比例是否达标
    
    Returns:
        {
            'valid': bool,
            'issues': List[str],
            'nan_counts': Dict[str, int],
            'inf_counts': Dict[str, int]
        }
    """
    issues = []
    nan_counts = {}
    inf_counts = {}
    
    # 关键指标列表
    critical_indicators = [
        'sma_20', 'sma_50', 'ema_12', 'ema_26',
        'macd', 'macd_signal', 'rsi'
    ]
    
    for col in critical_indicators:
        if col not in df.columns:
            issues.append(f"缺失关键指标: {col}")
            continue
        
        # NaN 检查
        nan_count = df[col].isna().sum()
        nan_counts[col] = nan_count
        
        # 全为 NaN？
        if nan_count == len(df):
            issues.append(f"{col} 全为 NaN")
        
        # Inf 检查
        inf_count = np.isinf(df[col]).sum()
        inf_counts[col] = inf_count
        
        if inf_count > 0:
            issues.append(f"{col} 包含 {inf_count} 个 Inf 值")
        
        # 有效数据比例检查（至少50%）
        valid_count = (~df[col].isna()).sum()
        valid_ratio = valid_count / len(df)
        
        if valid_ratio < 0.5:
            issues.append(
                f"{col} 有效数据不足: {valid_ratio:.1%} < 50%"
            )
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'nan_counts': nan_counts,
        'inf_counts': inf_counts
    }
```

---

### Phase 2: 决策逻辑增强（可选）

#### 2.1 数据质量评分

```python
# src/features/builder.py

def calculate_data_quality_score(self, market_state: Dict) -> float:
    """
    计算数据质量评分（0-100）
    
    因素：
    - 时间对齐（30分）
    - 价格一致性（30分）
    - 指标完整性（40分）
    
    Returns:
        质量评分（0-100）
    """
    score = 100.0
    
    # 时间对齐
    if 'alignment_check' in market_state:
        if not market_state['alignment_check']['aligned']:
            score -= 30
    
    # 价格一致性
    if 'price_consistency' in market_state:
        if not market_state['price_consistency']['consistent']:
            score -= 30
    
    # 指标完整性（从 timeframes 中提取）
    # TODO: 实现指标完整性检查
    
    return max(0, score)
```

#### 2.2 质量阈值过滤

```python
# run_live_trading.py: generate_signal()

def generate_signal(self, market_state: Dict) -> str:
    """生成交易信号（增加数据质量检查）"""
    
    # 数据质量检查
    quality_score = self.feature_builder.calculate_data_quality_score(market_state)
    
    MIN_QUALITY_THRESHOLD = 70  # 最低质量要求
    
    if quality_score < MIN_QUALITY_THRESHOLD:
        log.warning(
            f"⚠️  数据质量不足: {quality_score:.1f} < {MIN_QUALITY_THRESHOLD}"
        )
        return 'HOLD'  # 质量不达标，强制 HOLD
    
    # 原有的三层决策逻辑
    base_signal = self._basic_rule_signal(market_state)
    enhanced_signal = self._enhanced_rule_signal(market_state)
    risk_veto = self._risk_filter(market_state)
    
    return self._merge_signals(base_signal, enhanced_signal, risk_veto)
```

---

## 📊 测试验证计划

### 测试1: 多周期时间对齐

```python
# test_data_alignment.py

def test_multiframe_time_alignment():
    """测试多周期时间对齐"""
    
    # 场景1: 正常对齐（时间差 < 1分钟）
    states_aligned = {
        '5m': {'price': 50000, 'timestamp': '2025-12-18 10:00:00'},
        '15m': {'price': 50000, 'timestamp': '2025-12-18 10:00:30'},
        '1h': {'price': 50000, 'timestamp': '2025-12-18 10:01:00'}
    }
    
    result = builder._validate_multiframe_alignment(states_aligned)
    assert result['aligned'] == True
    
    # 场景2: 时间偏差过大（> 1小时）
    states_misaligned = {
        '5m': {'price': 50000, 'timestamp': '2025-12-18 10:00:00'},
        '15m': {'price': 50000, 'timestamp': '2025-12-18 10:00:00'},
        '1h': {'price': 50000, 'timestamp': '2025-12-18 08:00:00'}  # 2小时前
    }
    
    result = builder._validate_multiframe_alignment(states_misaligned)
    assert result['aligned'] == False
    assert len(result['warnings']) > 0
```

### 测试2: 价格一致性

```python
def test_multiframe_price_consistency():
    """测试多周期价格一致性"""
    
    # 场景1: 价格一致（偏差 < 0.5%）
    states_consistent = {
        '5m': {'price': 50000.0},
        '15m': {'price': 50050.0},  # +0.1%
        '1h': {'price': 49950.0}    # -0.1%
    }
    
    result = builder._validate_multiframe_prices(states_consistent)
    assert result['consistent'] == True
    
    # 场景2: 价格偏差过大（> 0.5%）
    states_inconsistent = {
        '5m': {'price': 50000.0},
        '15m': {'price': 50000.0},
        '1h': {'price': 51000.0}  # +2%，异常
    }
    
    result = builder._validate_multiframe_prices(states_inconsistent)
    assert result['consistent'] == False
    assert len(result['warnings']) > 0
```

### 测试3: 指标完整性

```python
def test_indicator_completeness():
    """测试指标完整性"""
    
    # 场景1: 正常数据
    df_normal = pd.DataFrame({
        'close': [50000 + i*10 for i in range(200)],
        'sma_20': [50000 + i*10 for i in range(200)],
        'rsi': [50 + i*0.1 for i in range(200)]
    })
    
    result = processor._validate_indicators(df_normal, 'BTCUSDT')
    assert result['valid'] == True
    
    # 场景2: SMA50 全为 NaN
    df_invalid = pd.DataFrame({
        'close': [50000 + i*10 for i in range(200)],
        'sma_50': [np.nan] * 200
    })
    
    result = processor._validate_indicators(df_invalid, 'BTCUSDT')
    assert result['valid'] == False
    assert 'sma_50 全为 NaN' in result['issues']
```

---

## 📁 需要修改的文件

### 立即执行（Phase 1）

1. **src/features/builder.py**
   - [ ] 添加 `_validate_multiframe_alignment()`
   - [ ] 添加 `_validate_multiframe_prices()`
   - [ ] 在 `build_market_context()` 中调用验证方法

2. **src/data/processor.py**
   - [ ] 添加 `_validate_indicators()`
   - [ ] 在 `process_klines()` 结尾调用验证

3. **test_data_quality.py**（新增）
   - [ ] 测试时间对齐
   - [ ] 测试价格一致性
   - [ ] 测试指标完整性

### 可选执行（Phase 2）

4. **src/features/builder.py**
   - [ ] 添加 `calculate_data_quality_score()`

5. **run_live_trading.py**
   - [ ] 在 `generate_signal()` 中添加质量检查
   - [ ] 记录质量评分到 Step5/Step6

---

## ✅ 验收标准

### 功能验收
1. [ ] 多周期时间对齐验证正常工作
2. [ ] 价格一致性检查能检测异常
3. [ ] 指标完整性验证能发现 NaN/Inf
4. [ ] 质量评分能正确反映数据状态

### 测试验收
1. [ ] 所有单元测试通过（test_data_quality.py）
2. [ ] 模拟异常数据场景全部覆盖
3. [ ] 真实数据验证通过

### 文档验收
1. [ ] DATA_FLOW_STRUCTURED.md 反映数据质量检查
2. [ ] 质量检查逻辑有详细注释

---

## 🎯 总结

### 问题本质

**决策逻辑的"硬"与数据质量的"软"之间存在鸿沟：**

```
决策层（刚性规则）
    ↑
    | ❌ 缺少质量保证层
    ↓
数据层（可能不完美）
```

### 解决方案

**引入数据质量保证层：**

```
决策层（刚性规则）
    ↑
质量保证层 ← 🆕 新增
    ↓
数据层（验证后可信）
```

### 优先级

1. **🔴 Critical**（立即执行）
   - 多周期价格一致性验证
   - 指标完整性检查

2. **🟡 Important**（建议执行）
   - 时间对齐验证
   - 质量评分机制

3. **🟢 Optional**（未来优化）
   - 自适应质量阈值
   - 数据质量监控看板

---

**最后更新**: 2025-12-19  
**状态**: Phase 1 待执行  
**优先级**: 🔴 Critical
