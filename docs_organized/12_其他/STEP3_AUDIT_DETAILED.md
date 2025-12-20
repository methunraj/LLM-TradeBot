# 步骤3（特征提取/快照）详细审计报告

**生成时间**: 2025-12-17  
**审计范围**: AI量化交易系统数据流转步骤3 - 特征提取与快照生成  
**审计人**: AI Copilot  
**相关代码**: `src/data/processor.py::extract_feature_snapshot`

---

## 一、步骤3输入、处理、输出详解

### 1.1 输入（来自步骤2）

**数据源**: `process_klines()` 输出的 DataFrame（包含原始K线 + 技术指标）

**输入结构**:
```python
pd.DataFrame with DatetimeIndex (timestamp)
Columns:
  - open, high, low, close, volume (原始K线)
  - sma_20, sma_50, ema_12, ema_26 (均线)
  - macd, macd_signal, macd_diff (MACD，已百分比归一化)
  - rsi (RSI指标)
  - bb_upper, bb_middle, bb_lower, bb_width (布林带)
  - atr (ATR，前期已修复0值问题)
  - volume_sma, volume_ratio (成交量指标)
  - vwap (20期滚动VWAP)
  - price_change_pct, high_low_range (价格变化)
  - is_valid (warm-up标记，前50根为False)
  - snapshot_id (快照ID，用于追踪)
```

**输入样例**（实盘BTC 5m数据，2025-12-17）:
```
时间: 2025-12-17 13:45:00
close: 87470.40
volume: 98.76
macd: 0.1264% (已归一化)
atr: 151.01
is_valid: True
```

### 1.2 处理逻辑（`extract_feature_snapshot`）

#### 阶段1: 时间对齐与缺口处理
```python
def _check_time_gaps(df, freq_minutes=5, allowed_gap_bars=2):
    """
    - 重新索引为完整5分钟间隔
    - 检测缺失的时间戳
    - 对 gap <= 2 根的缺口进行线性插值
    - 对 gap > 2 根的缺口标记为 invalid（不插值）
    - 返回 is_imputed 标记
    """
```

**修复点**:
- ✅ 插值前调用 `infer_objects()` 减少类型推断警告
- ✅ 限制插值范围（`limit=allowed_gap_bars`），避免大缺口引入未来信息
- ✅ 标记 `is_imputed=True` 的行，下游可选择过滤

#### 阶段2: 窗口特征计算（Rolling Window）
```python
lookback = 48  # 可配置，默认48根K线（5m = 4小时）
min_fraction = 0.5  # 最少需要 50% 的窗口数据
```

**计算特征列表**:
1. **基础特征**:
   - `return_pct`: 收益率（%），已clip到 [-1e4, 1e4] 防止极端值
   - `log_return`: 对数收益率（安全处理 close<=0 情况）
   - `rolling_vol`: 滚动波动率（窗口内return_pct的std）
   - `rolling_mean_price`, `rolling_median_price`: 滚动均值/中位数

2. **动量特征**:
   - `momentum_1`: 1期动量
   - `momentum_12`: 12期动量

3. **技术指标相对化**（核心修复）:
   - `macd_pct`, `macd_signal_pct`, `macd_diff_pct`: 直接使用步骤2已归一化的字段（避免重复计算）
   - `atr_pct`: ATR / close * 100
   - `vwap_rel`: (close - vwap) / vwap
   - `bb_width_pct`: bb_width * 100（安全除法，分母=1.0）
   - `high_low_range_pct`: 直接使用步骤2已计算的百分比

4. **成交量特征**:
   - `volume_z`: 滚动z-score = (volume - rolling_mean) / rolling_std
   - `volume_ratio`: 直接使用步骤2字段（默认1.0）

5. **极值处理（Winsorize）**:
   - 对 `return_pct`, `log_return`, `momentum_1`, `momentum_12`, `volume_z` 按 1%-99% 分位数截断

6. **全局inf清理**:
   - 所有 inf/-inf 替换为 NaN，保证数值稳定性

#### 阶段3: 有效性标记
```python
is_feature_valid = (
    src_is_valid  # 步骤2的 warm-up 标记
    & has_critical  # 关键字段非NaN（close/volume/macd_pct/atr_pct）
    & has_enough_history  # 窗口内样本 >= min_periods
    & (~is_imputed)  # 非插值产生
)
```

#### 阶段4: 元数据注入
- `feature_version`: 特征版本标识（v1）
- `processor_version`: 处理器版本（processor_v1）
- `source_snapshot_id`: 引用步骤2的快照ID
- `warm_up_bars_remaining`: 距离完整窗口还差多少根（0表示已满足）
- `is_imputed`: 是否为插值产生的行

### 1.3 输出

**输出结构**: `pd.DataFrame` (与输入相同索引)

**输出字段**（24列）:
```python
[
  'close', 'volume',  # 原始字段
  'return_pct', 'log_return', 'rolling_vol',  # 基础特征
  'rolling_mean_price', 'rolling_median_price',
  'momentum_1', 'momentum_12',  # 动量
  'macd_pct', 'macd_signal_pct', 'macd_diff_pct',  # MACD（相对值）
  'atr_pct',  # ATR（相对值）
  'vwap_rel',  # VWAP相对差
  'bb_width_pct', 'high_low_range_pct',  # 布林带/振幅
  'volume_z', 'volume_ratio',  # 成交量
  'is_feature_valid',  # 有效性标记
  'warm_up_bars_remaining',  # warm-up剩余
  'feature_version', 'source_snapshot_id', 'processor_version',  # 元数据
  'is_imputed'  # 插值标记
]
```

**实盘输出样例**（BTC 5m，2025-12-17 13:45）:
```
close: 87470.40
macd_pct: 0.1264%
atr_pct: 0.1726%
vwap_rel: 0.0046
volume_z: 0.95
return_pct: 0.1056%
is_feature_valid: True
warm_up_bars_remaining: 0
feature_version: v1
is_imputed: False
```

**数值稳定性验证**:
- ✅ 无 inf 值
- ✅ NaN占比: 11.47%（主要在前期warm-up阶段）
- ✅ 有效率: 50%（100根数据中50根通过warm-up）

---

## 二、发现的问题与修复

### 问题A: 时间缺口未标记或盲目插值导致未来信息泄露

**现象**: 原始代码直接 reindex 后全量插值，可能在大缺口（如周末/节假日停盘）填充虚假数据。

**根因**: 未区分小缺口（可安全插值）与大缺口（应标记invalid）。

**修复**:
```python
# 仅对 gap <= allowed_gap_bars (默认2) 的缺口插值
df_re.interpolate(method='time', limit=allowed_gap_bars, inplace=True)
# 标记插值行
imputed_mask = orig_na & df_re['close'].notna()
df_re['is_imputed'] = imputed_mask
# 下游过滤：is_feature_valid 排除 is_imputed=True 的行
```

**验证**: 测试用例 `test_time_gaps_marked_and_imputed` 通过 ✅

---

### 问题B: 除以0或非常小数值导致 inf/NaN

**现象**: 
- `vwap_rel = (close - vwap) / vwap`，当vwap=0时产生inf
- `volume_z = (vol - mean) / std`，当std=0时产生inf

**根因**: 直接除法未加保护。

**修复**:
```python
def _safe_div(numer, denom, eps=1e-9, fill=0.0):
    # 支持标量或Series作为分母
    denom_safe = max(denom, eps)  # 或 denom.clip(lower=eps)
    res = numer / denom_safe
    res = res.where(denom >= eps, fill)  # 分母过小时填充默认值
    return res
```

**验证**: 测试用例 `test_divide_by_zero_safety` 通过 ✅

---

### 问题C: 直接使用绝对MACD/ATR数值（scale依赖价格级别）

**现象**: BTC在8万价位时，MACD绝对值可达几百，与1万价位时不可比。

**根因**: 未归一化为相对值。

**修复**:
- 步骤2已将 macd 归一化为百分比（`macd / close * 100`）
- 步骤3优先使用步骤2的归一化字段，避免重复计算
- `atr_pct = atr / close * 100`

**验证**: 
- 测试用例 `test_macd_and_atr_percent_normalization` 通过 ✅
- 实盘验证：macd_pct=0.1264%，atr_pct=0.1726%（合理范围）

---

### 问题D: 极端值未处理导致后续计算失真

**现象**: 
- 价格跳空产生 return_pct > 10000%
- Winsorize失效（极端值拉高分位数阈值）

**根因**: 未在 winsorize 前进行硬截断。

**修复**:
```python
# 先 clip 到合理上限
features['return_pct'] = features['return_pct'].clip(lower=-1e4, upper=1e4)
# 再 winsorize
features['return_pct'] = self._winsorize(features['return_pct'], 0.01, 0.99)
# 全局清理 inf
features.replace([np.inf, -np.inf], np.nan, inplace=True)
```

**验证**: 测试用例 `test_outlier_winsorize` 通过 ✅

---

### 问题E: 未标记warm-up状态导致前期特征不稳定

**现象**: 前48根K线（lookback窗口）的滚动特征基于不足样本计算，方差大。

**根因**: 未输出 `warm_up_bars_remaining` 和 `is_feature_valid` 供下游过滤。

**修复**:
```python
# 计算窗口内有效计数
window_count = features['close'].rolling(window=L, min_periods=1).count()
features['warm_up_bars_remaining'] = (L - window_count).clip(lower=0).astype(int)

# 合成有效性标记
is_feature_valid = (
    src_is_valid  # 步骤2已标记前50根invalid
    & (window_count >= min_periods)  # 窗口样本充足
    & has_critical  # 关键字段非NaN
    & (~is_imputed)  # 非插值
)
```

**验证**: 
- 测试用例 `test_warmup_flag` 通过 ✅
- 实盘验证：有效率=50%（100根数据中50根通过）

---

### 问题F: 缺少版本与可追溯性信息

**现象**: 特征计算逻辑变更后，无法回溯历史特征是用哪个版本生成的。

**根因**: 未注入 `feature_version` / `processor_version` / `source_snapshot_id`。

**修复**:
```python
features['feature_version'] = feature_version  # v1
features['processor_version'] = self.PROCESSOR_VERSION  # processor_v1
features['source_snapshot_id'] = df_checked['snapshot_id']  # 引用步骤2
```

**验证**: 测试用例 `test_persistence_schema_and_versioning` 通过 ✅

---

## 三、自动化测试结果

**测试文件**: `tests/test_step3_features.py`

**测试用例**（6个，全部通过 ✅）:
1. `test_time_gaps_marked_and_imputed`: 时间缺口标记与插值
2. `test_divide_by_zero_safety`: 除以0安全处理
3. `test_warmup_flag`: warm-up标记正确性
4. `test_macd_and_atr_percent_normalization`: MACD/ATR百分比归一化
5. `test_outlier_winsorize`: 极端值winsorize
6. `test_persistence_schema_and_versioning`: 持久化schema与版本信息

**运行结果**:
```bash
pytest tests/test_step3_features.py -q
6 passed, 9 warnings in 1.13s
```

---

## 四、实盘验证结果

**验证环境**: 
- 交易对: BTCUSDT
- 时间周期: 5m
- 数据量: 100根K线
- 验证时间: 2025-12-17 21:45

**验证结果**:

1. **数据完整性**: ✅
   - 输入: 100根K线
   - 处理后: 100行特征数据
   - 特征列: 24列（符合设计）

2. **数值稳定性**: ✅
   - 无 inf 值
   - NaN占比: 11.47%（可接受，主要在warm-up期）

3. **特征有效率**: ✅
   - 有效行数: 50/100
   - 有效率: 50%（符合lookback=48的预期）

4. **关键特征数值**（最新行）: ✅
   ```
   macd_pct: 0.1264%  (合理，小于1%)
   atr_pct: 0.1726%   (合理，波动率百分比)
   volume_z: 0.95     (合理，z-score)
   return_pct: 0.1056% (合理，5分钟收益率)
   ```

5. **元数据完整性**: ✅
   - feature_version: v1
   - processor_version: processor_v1
   - is_feature_valid: True
   - warm_up_bars_remaining: 0
   - is_imputed: False

---

## 五、专业量化意义

### 5.1 特征工程改进

**相对化处理**:
- 使MACD/ATR等指标在不同价格级别下可比（BTC 8万 vs 1万）
- 模型泛化能力提升，不依赖绝对价格水平

**Winsorize + Clip**:
- 减少极端值对模型训练的干扰
- 提高回测与实盘一致性（避免回测中极端outlier拟合）

**滚动窗口 vs 全局统计**:
- 避免数据泄露（训练集用测试集统计量标准化）
- 适应市场状态变化（波动率regime shift）

### 5.2 风控与合规

**is_feature_valid 标记**:
- 强制过滤不稳定数据，避免warm-up期错误信号
- 减少过拟合风险（训练时只用valid=True的样本）

**is_imputed 标记**:
- 审计时可追溯哪些数据点是插值产生
- 合规要求下可选择完全排除插值数据

**版本追踪**:
- 满足金融监管对模型可解释性的要求
- 便于A/B测试不同feature_version的效果

### 5.3 生产部署建议

**实时计算优化**:
- 使用增量更新（rolling buffer）而非全量重算
- 缓存滚动统计量（mean/std）的中间状态

**监控指标**:
- 每日统计 `is_feature_valid` 占比，低于阈值（如30%）告警
- 监控 NaN占比，突增可能表明数据源异常
- 跟踪 `is_imputed` 比例，过高需检查数据质量

**版本迁移**:
- 新版本特征先shadow-run两周，对比分布漂移
- 使用 feature_version 做灰度切换（部分流量用v1，部分用v2）

---

## 六、已知局限与后续优化方向

### 6.1 当前局限

1. **窗口大小固定**:
   - 当前 lookback=48 对所有市场状态一致
   - 高波动期可能需要更短窗口（如24），低波动期需要更长（如96）

2. **特征选择未自动化**:
   - 24个特征中可能存在冗余（如 momentum_1 vs return_pct）
   - 建议后续用 feature importance / SHAP 筛选

3. **插值策略简单**:
   - 当前仅线性插值，对价格可能不合理（指数插值更佳）
   - 建议区分价格字段（指数插值）与成交量字段（线性或0填充）

### 6.2 后续优化

1. **自适应窗口**:
   ```python
   lookback = adaptive_window(volatility_regime)
   # 高波动: 24, 正常: 48, 低波动: 96
   ```

2. **特征降维**:
   - PCA / Autoencoder 提取主成分
   - 减少模型输入维度，加速推理

3. **异常检测增强**:
   - 引入 Isolation Forest 检测多维异常（当前仅单维winsorize）
   - 标记异常样本为 `is_anomaly=True`

4. **持久化优化**:
   - 当前返回全表，建议分离"训练模式"（全表）与"推理模式"（仅最新行）
   - 使用 Parquet 分区存储（按日期/symbol），加速查询

---

## 七、总结

**修复点数**: 6个主要问题（A-F）

**测试覆盖**: 6个自动化测试用例，全部通过 ✅

**实盘验证**: 通过 ✅（BTC 5m数据，无inf，有效率50%）

**代码质量**:
- 数值稳定性: ✅（安全除法、inf清理、clip+winsorize）
- 可追溯性: ✅（feature_version、processor_version、source_snapshot_id）
- 鲁棒性: ✅（warm-up标记、is_imputed标记、关键字段校验）

**建议下一步**:
1. 将修复提交为 git commit
2. 生成 STEP3_FIXES_COMPLETED.md 供非技术人员阅读
3. 在生产环境 shadow-run 两周，监控分布漂移与特征有效率

---

**审计结论**: 步骤3修复完成且质量达标，可投入生产使用。
