# 🔧 架构修复快速参考指南

**用途**: 快速查阅所有架构修复点，确保后续开发遵循正确原则  
**最后更新**: 2025-12-18  

---

## ⚡ 核心原则（必须遵守）

### 1️⃣ **数据获取原则**
```python
# ✅ 正确：每个时间周期独立从 API 获取
klines_5m = client.get_klines(symbol, '5m', limit=300)
klines_15m = client.get_klines(symbol, '15m', limit=300)
klines_1h = client.get_klines(symbol, '1h', limit=300)

# ❌ 错误：从单一周期转换
klines_5m = client.get_klines(symbol, '5m', limit=300)
klines_15m = resample_klines(klines_5m, '15m')  # ❌ 绝不这样做！
```

### 2️⃣ **K线验证原则**
```python
# ✅ 正确：K线是市场事实，绝不修改价格
validator = KlineValidator()
klines, report = validator.validate_and_clean_klines(
    klines, 
    symbol, 
    action='remove'  # 只删除无效数据，不修改价格
)

# ❌ 错误：裁剪/修正价格
# 绝不做：MAD裁剪、异常值平滑、价格修正
```

### 3️⃣ **Warmup 期原则**
```python
# ✅ 正确：105 根（MACD完全收敛）
WARMUP_PERIOD = 105  # EMA26(78) + Signal(27)

# ❌ 错误：50 根（不足）
WARMUP_PERIOD = 50  # MACD未收敛，前期指标有偏差
```

### 4️⃣ **风控参数原则**
```python
# ✅ 正确：动态获取交易所规则
min_notional = client.get_symbol_min_notional(symbol, default=5.0)

# ❌ 错误：硬编码
MIN_NOTIONAL = 10.0  # 可能不符合交易所实时规则
```

### 5️⃣ **信号逻辑原则**
```python
# ✅ 正确：明确定义
LONG = "做多（看涨）"
SHORT = "做空（看跌）"
HOLD = "观望（既不做多也不做空）"  # 明确语义

# ❌ 错误：模糊定义
HOLD = "维持现有仓位"  # 不明确，容易混淆
```

---

## 📋 关键配置清单

### run_live_trading.py
```python
# K线获取数量
KLINE_LIMIT = 300  # 所有周期统一

# 多周期独立获取
klines_5m = self.client.get_klines(symbol, '5m', limit=300)
klines_15m = self.client.get_klines(symbol, '15m', limit=300)
klines_1h = self.client.get_klines(symbol, '1h', limit=300)

# MIN_NOTIONAL 动态获取
self.min_notional = self.client.get_symbol_min_notional(symbol, default=5.0)
```

### src/data/processor.py
```python
# Warmup 期配置
WARMUP_PERIOD = 105  # MACD完全收敛所需

# 技术指标参数（已标准化）
INDICATOR_PARAMS = {
    'sma': [20, 50],
    'ema': [12, 26],
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'rsi': {'period': 14},
    'bollinger': {'period': 20, 'std_dev': 2},
    'atr': {'period': 14},
    'volume_sma': {'period': 20}
}

# K线验证
validator = KlineValidator()  # 不裁剪价格，只删除无效数据
```

---

## 🧪 验证命令

### 完整验证
```bash
python verify_all_architecture_fixes.py
```

### 单项验证
```bash
# Warmup 期
python test_warmup_period_fix.py

# K线验证器
python test_kline_validator.py

# MIN_NOTIONAL
python verify_min_notional_docs.py
```

---

## 📊 数据流关键节点

### Step0: 数据获取
- ✅ 三个周期独立获取（5m/15m/1h）
- ✅ 每个周期 300 根K线

### Step2: 技术指标
- ✅ K线验证不裁剪价格
- ✅ Warmup 期 105 根
- ✅ 有效数据 195 根

### Step4: 趋势判断
- ✅ 只使用 is_valid=True 的数据
- ✅ MACD 完全收敛

### Step7: 风控检查
- ✅ MIN_NOTIONAL 动态获取
- ✅ 默认值 5.0 USDT

---

## 🚨 常见错误（避免）

### ❌ 错误1: 单周期转换多周期
```python
# ❌ 绝对不要这样做
df_15m = df_5m.resample('15T').agg({...})
```

### ❌ 错误2: 裁剪K线价格
```python
# ❌ 绝对不要这样做
df['close'] = np.where(
    abs(df['close'] - median) > 3*MAD,
    median,  # ❌ 修改价格！
    df['close']
)
```

### ❌ 错误3: Warmup 期不足
```python
# ❌ 不足
WARMUP_PERIOD = 50  # MACD未收敛

# ✅ 正确
WARMUP_PERIOD = 105  # MACD完全收敛
```

### ❌ 错误4: 硬编码交易规则
```python
# ❌ 不灵活
MIN_NOTIONAL = 10.0

# ✅ 动态获取
min_notional = client.get_symbol_min_notional(symbol, default=5.0)
```

---

## 📚 文档索引

### 问题分析文档
- `WARMUP_PERIOD_ISSUE.md` - Warmup期问题详细分析
- `MACD_MODIFICATION_ISSUE.md` - MACD定义问题

### 修复报告文档
- `WARMUP_INSUFFICIENT_FIX.md` - Warmup期修复报告
- `K_LINE_VALIDATION_CRITICAL_FIX.md` - K线验证修复报告
- `MIN_NOTIONAL_DYNAMIC_FIX.md` - MIN_NOTIONAL修复报告

### 主文档
- `DATA_FLOW_STRUCTURED.md` - 数据流主文档（权威）
- `ARCHITECTURE_ISSUES_SUMMARY.md` - 架构问题总结
- `ARCHITECTURE_FIX_FINAL_SUMMARY.md` - 修复最终总结

---

## ✅ 开发检查清单

开发新功能前，请确认：

- [ ] 多周期数据是否独立获取？
- [ ] K线验证是否只删除无效数据（不修改价格）？
- [ ] Warmup 期是否 >= 105 根？
- [ ] 是否只使用 is_valid=True 的数据做决策？
- [ ] 交易规则参数是否动态获取？
- [ ] 代码逻辑是否与文档一致？

---

## 🎯 核心文件清单

### 关键代码文件
| 文件 | 作用 | 关键配置 |
|-----|------|---------|
| `run_live_trading.py` | 实盘主入口 | limit=300, 独立获取 |
| `src/data/processor.py` | 指标计算 | WARMUP_PERIOD=105 |
| `src/data/kline_validator.py` | K线验证 | 不裁剪价格 |
| `src/api/binance_client.py` | API接口 | get_symbol_min_notional |

### 测试文件
| 文件 | 验证内容 |
|-----|---------|
| `test_warmup_period_fix.py` | Warmup期105根 |
| `test_kline_validator.py` | K线不裁剪 |
| `verify_all_architecture_fixes.py` | 完整验证 |

---

**快速参考**: 有问题先查这个文档，然后看主文档 `DATA_FLOW_STRUCTURED.md`
