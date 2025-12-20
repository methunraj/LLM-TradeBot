# 数据流转问题修复计划

## 📋 审计问题清单

根据专业审计报告，发现以下需要修复的问题：

### 🚨 高风险问题（必须修复）

1. **异常检测结果前后逻辑冲突**
   - 症状：validator 报告有异常，process_klines 报告 0 个异常
   - 风险：回测/实盘不可对齐
   - 优先级：P0

2. **对合约K线使用 interpolate 是危险操作**
   - 症状：使用插值处理异常值
   - 风险：制造虚假价格路径，ATR/波动率被系统性低估
   - 优先级：P0

### ⚠️ 中风险问题（建议修复）

3. **多周期快照时间不一致**
   - 症状：5m/15m/1h 时间戳不对齐
   - 风险：多周期信号拼接错位
   - 优先级：P1

4. **Z-score 用在金融时间序列上不稳定**
   - 症状：金融数据非正态，Z-score 误判
   - 风险：大行情被误判，平稳行情检测不出
   - 优先级：P1

5. **指标 warm-up 边界未明确**
   - 症状：前 50 根数据指标不稳定但未标记
   - 风险：前期信号是"脏信号"
   - 优先级：P2

## 🔧 修复方案

### 问题 1：异常检测逻辑统一

**修改文件：** `src/data/validator.py`, `src/data/processor.py`

**修改内容：**
```python
# 1. 统一异常检测入口，只在 validator 中检测
# 2. 返回详细的异常信息：
#    - raw_anomaly_count: 原始异常数量
#    - cleaned_anomaly_count: 清洗后剩余异常
#    - interpolated_points: 被插值的点
#    - method_used: 处理方法
```

### 问题 2：替换 interpolate 为更安全的方法

**修改文件：** `src/data/validator.py`

**修改内容：**
```python
# 对不同类型的异常使用不同处理方法：
# - high/low 异常: clip 到邻近最大/最小值
# - open/close 异常: 使用 prev_close
# - 成交量异常: 置为 NaN
# - 超阈值异常: 整根 K 线 drop
```

### 问题 3：多周期时间对齐

**修改文件：** `run_with_pipeline_logs.py`

**修改内容：**
```python
# 1. 设定一个 anchor_time
# 2. 所有周期只取 <= anchor_time 的已收盘 K 线
# 3. 禁止使用未完全收盘的 K 线
```

### 问题 4：替换 Z-score 为更稳健的方法

**修改文件：** `src/data/validator.py`

**修改内容：**
```python
# 使用以下方法替代 Z-score：
# 1. Rolling MAD (Median Absolute Deviation)
# 2. Returns-based filter (涨跌幅检测)
# 3. High/Low 相对 Close 比例
# 4. 组合判断，提高准确性
```

### 问题 5：指标 warm-up 边界标记

**修改文件：** `src/data/processor.py`

**修改内容：**
```python
# 1. 计算 min_valid_index
# 2. 在 DataFrame 中添加 is_valid 列
# 3. 日志中明确标记 warm-up 期
# 4. 特征提取时只使用 valid 数据
```


## 📝 实施步骤

1. ✅ 问题 2：修复异常值处理方法（interpolate → clip/drop）
2. ✅ 问题 4：替换 Z-score 为 MAD + Returns filter
3. ✅ 问题 1：统一异常检测逻辑
4. ✅ 问题 5：添加指标 warm-up 标记
5. ✅ 问题 3：多周期时间对齐
6. ✅ 下游模块强制使用有效数据
7. 🔄 测试验证（进行中）

## 🎯 预期效果

修复后的系统应该具备：
- ✅ 异常检测逻辑前后一致
- ✅ 不会制造虚假价格路径
- ✅ 多周期信号严格对齐
- ✅ 异常检测更准确
- ✅ 指标 warm-up 边界明确
- ✅ 日志与实际处理完全一致
- ✅ 特征提取只使用有效数据

## 📊 验证标准

- ✅ validator 和 processor 的异常计数一致（通过详细日志）
- ✅ 没有使用 interpolate（已改为 clip/drop）
- ✅ 多周期时间戳对齐（实现 anchor_time）
- ✅ 异常检测使用 MAD/Returns/HL-range
- ✅ 有明确的 min_valid_index（已实现）
- ✅ 特征提取有 is_valid 检查
- 🔄 实盘运行无逻辑错误（待持续验证）

## ✨ 最新修复（2025-12-17）

### 1. 完善 warm-up 期标记
- 在 `processor.py` 中实现 `_mark_warmup_period()` 和 `_get_min_valid_index()`
- 计算逻辑：取 SMA50、MACD(26+9)、ATR14 的最大值 = 50
- 添加 `is_valid` 列标记有效数据
- 快照中包含 `min_valid_index` 信息

### 2. 特征提取强制检查有效性
- 在 `run_with_pipeline_logs.py` 的 `_extract_and_log_features()` 中添加：
  - 检查 `is_valid` 列是否存在
  - 检查最后一行数据是否在 warm-up 期
  - 添加 `warmup_status` 字段到特征中
  - 如果数据在 warm-up 期，输出明确警告

### 3. 多周期 anchor 时间对齐
- 实现 `_align_klines_to_anchor()` 函数
- 获取当前时间作为 anchor_time
- 过滤所有未完全收盘的K线（close_time <= anchor_time）
- 确保 5m/15m/1h 使用同一时间基准
- 日志输出对齐前后的K线数量

