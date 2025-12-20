# 🎯 OBV特征未归一化问题 - 执行摘要

**日期**: 2025-12-18  
**问题编号**: #9  
**严重程度**: 🟡 中危  
**状态**: ⚠️ 待修复

---

## 📋 问题总结

### 现象
OBV（On Balance Volume）指标未实现，且文档中描述的实现方案存在**特征尺度爆炸**风险。

### 诊断结果
运行 `diagnose_obv_issue.py` 发现：

| K线数量 | OBV vs RSI | OBV vs MACD% | 严重性 |
|---------|-----------|-------------|--------|
| 50 | **23倍** | **1009倍** | 🔴 高 |
| 100 | **13倍** | **215倍** | 🔴 高 |
| 1000 | **74倍** | **2297倍** | 🔴 极高 |

**示例对比**:
```
rsi:            65.0        ✅ 正常
macd_pct:       0.5         ✅ 正常
obv_raw:        8532.0      ❌ 失控（131倍）
obv_change_pct: 2.5         ✅ 正常（归一化后）
obv_zscore:     1.8         ✅ 正常（归一化后）
```

---

## 🚨 核心问题

1. **OBV是累加量** → 数值随历史长度无限增长
2. **量级不可控** → 可能比其他特征大100~2000倍
3. **模型失真** → 梯度计算被OBV主导，其他特征信号淹没
4. **跨数据集不可比** → 同样市场状态，不同历史长度OBV完全不同

---

## ✅ 解决方案

### 3步修复（详见 `OBV_FIX_SUMMARY.md`）

**Step1: 实现OBV计算**（Step2阶段）
```python
# src/data/processor.py::_calculate_indicators()
df['obv_direction'] = np.sign(df['close'].diff().fillna(0))
df['obv_raw'] = (df['volume'] * df['obv_direction']).cumsum()
```

**Step2: 归一化**（Step3阶段）
```python
# src/data/processor.py::extract_feature_snapshot()

# 方法1: 变化率%（反映短期动态）
features['obv_change_pct'] = (obv.diff() / (obv.shift(1).abs() + 1e-9) * 100).clip(-100, 100)

# 方法2: Z-score（反映相对强度）
features['obv_zscore'] = ((obv - obv.rolling(48).mean()) / obv.rolling(48).std()).clip(-5, 5)

# ❌ 禁止直接使用原始OBV
```

**Step3: 自动验证**
```python
# 添加特征尺度检测
def _validate_feature_scales(self, features):
    for col in feature_cols:
        if abs_max > 1000:
            log.warning(f"特征 '{col}' 量级过大")
        if 'obv' in col and 'raw' in col:
            log.error(f"禁止使用原始OBV: '{col}'")
```

---

## 📊 预期效果

**修复前**:
```
特征       数值      问题
obv_raw    8532.0    ❌ 比其他特征大131倍
```

**修复后**:
```
特征             数值      状态
obv_change_pct   2.5       ✅ 尺度正常
obv_zscore       1.8       ✅ 尺度正常
```

---

## 🛠️ 实施清单

- [ ] **代码修改**（2-3小时）
  - [ ] Step2: 添加OBV计算（10分钟）
  - [ ] Step3: 添加归一化特征（30分钟）
  - [ ] 添加特征尺度验证（30分钟）
  - [ ] 创建单元测试（1小时）

- [ ] **验证测试**
  - [x] 运行诊断脚本 `diagnose_obv_issue.py` ✅
  - [ ] 运行单元测试 `test_obv_normalization.py`
  - [ ] 实际数据验证

- [ ] **文档更新**
  - [ ] 更新 `DATA_FLOW_STRUCTURED.md`
  - [x] 创建 `OBV_NORMALIZATION_ISSUE.md` ✅
  - [x] 创建 `OBV_FIX_SUMMARY.md` ✅
  - [x] 更新 `ARCHITECTURE_ISSUES_SUMMARY.md` ✅

---

## 🔗 相关文档

| 文档 | 说明 |
|------|------|
| `OBV_NORMALIZATION_ISSUE.md` | 完整问题分析 |
| `OBV_FIX_SUMMARY.md` | 详细修复方案与代码 |
| `diagnose_obv_issue.py` | 自动化诊断脚本 |
| `data/diagnostic_reports/obv_diagnostic_*.json` | 诊断结果数据 |
| `ARCHITECTURE_ISSUES_SUMMARY.md` | 问题#9汇总 |

---

## 🎯 下一步

1. **优先级**: 🔴 高（建议下一迭代完成）
2. **责任人**: 数据处理模块负责人
3. **预计时间**: 2-3小时
4. **风险**: 🟢 低（纯新增功能）

**建议实施顺序**:
```
诊断验证 → 实现OBV → 实现归一化 → 添加验证 → 单元测试 → 更新文档 → 代码审查
```

---

✅ **诊断完成** | ⚠️ **待实施** | 📅 2025-12-18
