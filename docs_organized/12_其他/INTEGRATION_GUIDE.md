# 数据对齐优化 - 集成指南

本文档提供将数据对齐优化集成到现有交易系统的详细步骤。

---

## 📋 概述

### 当前问题
- 系统在实盘交易中所有周期都使用 `iloc[-2]`（最后一根完成的K线）
- 导致1h周期数据滞后超过**111分钟**（近2小时）
- 多周期数据时间错位达**105分钟**

### 解决方案
- 引入配置化的实时/滞后模式切换
- 短周期（5m/15m）可选择使用实时K线（`iloc[-1]`）
- 长周期（1h/4h）保持使用完成K线（`iloc[-2]`）
- 增加数据时间戳日志和滞后告警

---

## 🛠️ 集成步骤

### 步骤1: 安装依赖（如需要）

```bash
# 如果项目还没有 PyYAML
pip install pyyaml
```

### 步骤2: 配置数据对齐模式

编辑 `config/data_alignment.yaml`:

```yaml
# 推荐配置：实盘安全模式
mode: 'live_safe'

timeframe_settings:
  5m:
    use_realtime: true           # 启用实时K线
    min_completion_pct: 30       # 至少完成30%（1.5分钟）
    lag_warning_threshold: 10    # 滞后超过10分钟告警
  
  15m:
    use_realtime: true
    min_completion_pct: 40       # 至少完成40%（6分钟）
    lag_warning_threshold: 20
  
  1h:
    use_realtime: false          # 保持使用完成K线
    lag_warning_threshold: 120   # 1小时周期允许更高滞后

lag_detection:
  enabled: true
  warning_threshold_minutes: 30
  time_gap_threshold_minutes: 60
```

### 步骤3: 修改特征构建器

编辑 `src/features/builder.py`，找到获取最新K线的代码（大约在 `build_features()` 方法中）：

#### 当前代码（示例）：
```python
def build_features(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    features = {}
    
    for timeframe, df in data.items():
        # 固定使用 iloc[-2]
        latest = df.iloc[-2]
        
        # ... 提取特征
        features[timeframe] = {
            'close': latest['close'],
            'sma_20': latest['sma_20'],
            # ...
        }
    
    return features
```

#### 修改后的代码：
```python
from src.utils.data_alignment import DataAlignmentHelper

class FeatureBuilder:
    def __init__(self, config):
        self.config = config
        # 初始化数据对齐助手
        self.alignment_helper = DataAlignmentHelper()
    
    def build_features(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        features = {}
        
        for timeframe, df in data.items():
            # 使用数据对齐助手获取K线
            latest, metadata = self.alignment_helper.get_aligned_candle(df, timeframe)
            
            # 记录元数据（重要！）
            self.logger.info(
                f"[{timeframe}] 数据时间: {metadata['timestamp'].strftime('%H:%M:%S')}, "
                f"滞后: {metadata['lag_minutes']:.1f}分钟, "
                f"模式: {'实时' if metadata['is_realtime'] else '滞后'}"
            )
            
            # 提取特征
            features[timeframe] = {
                'close': latest['close'],
                'sma_20': latest['sma_20'],
                # ... 其他特征
                
                # 添加时间戳和元数据（供后续步骤使用）
                'timestamp': metadata['timestamp'],
                'lag_minutes': metadata['lag_minutes'],
                'is_realtime': metadata['is_realtime'],
            }
        
        return features
```

### 步骤4: 增强Step4多周期评分

编辑 `src/strategies/step4_multi_timeframe_score.py`：

```python
def calculate(self, features: Dict[str, Dict]) -> Dict:
    """计算多周期评分"""
    
    # 记录多周期时间状态
    self._log_timeframe_alignment(features)
    
    # ... 原有的评分逻辑
    
    return scores

def _log_timeframe_alignment(self, features: Dict[str, Dict]):
    """记录多周期时间对齐状态"""
    
    # 收集时间戳
    timestamps = []
    for timeframe, feat in features.items():
        if 'timestamp' in feat:
            timestamps.append((timeframe, feat['timestamp'], feat.get('lag_minutes', 0)))
    
    if not timestamps:
        return
    
    # 排序并显示
    timestamps.sort(key=lambda x: x[1], reverse=True)
    
    self.logger.info("=" * 60)
    self.logger.info("多周期数据时间状态:")
    for tf, ts, lag in timestamps:
        self.logger.info(f"  [{tf:3s}] {ts.strftime('%Y-%m-%d %H:%M:%S')} (滞后 {lag:5.1f}分钟)")
    
    # 计算时间错位
    earliest = min([t[1] for t in timestamps])
    latest = max([t[1] for t in timestamps])
    time_gap = (latest - earliest).total_seconds() / 60
    
    self.logger.info(f"  时间错位: {time_gap:.1f}分钟")
    
    if time_gap > 60:
        self.logger.warning(
            f"  ⚠️ 时间错位超过1小时！可能影响决策准确性"
        )
    
    self.logger.info("=" * 60)
```

### 步骤5: 增强Step6综合信号

编辑 `src/strategies/step6_integrated_signal.py`：

```python
def generate_signal(self, all_data: Dict) -> Dict:
    """生成交易信号"""
    
    # 检查数据时间错位
    features = all_data.get('features', {})
    self._check_data_alignment(features)
    
    # ... 原有的信号生成逻辑
    
    return signal

def _check_data_alignment(self, features: Dict[str, Dict]):
    """检查并告警数据对齐问题"""
    
    max_lag = 0
    for timeframe, feat in features.items():
        lag = feat.get('lag_minutes', 0)
        max_lag = max(max_lag, lag)
        
        # 单个周期滞后告警
        if lag > 120:  # 超过2小时
            self.logger.warning(
                f"🔴 [{timeframe}] 数据严重滞后: {lag:.1f}分钟"
            )
    
    # 记录到信号元数据
    if hasattr(self, 'signal_metadata'):
        self.signal_metadata['max_data_lag_minutes'] = max_lag
```

### 步骤6: 更新主程序

编辑 `run_live_trading.py`（如果需要显式加载配置）：

```python
from src.utils.data_alignment import DataAlignmentHelper

def main():
    # ... 初始化配置
    
    # 显示数据对齐配置
    alignment_helper = DataAlignmentHelper()
    logger.info(f"数据对齐模式: {alignment_helper.mode}")
    
    # ... 启动交易循环
```

---

## 🧪 测试与验证

### 测试1: 运行诊断工具

```bash
python diagnose_data_lag.py
```

检查输出，确认滞后情况和建议配置。

### 测试2: 纸面交易测试

```bash
# 使用小仓位或模拟模式
python run_live_trading.py --mode paper
```

观察日志中的时间戳和滞后信息：
```
[5m ] 数据时间: 16:52:00, 滞后: 1.2分钟, 模式: 实时
[15m] 数据时间: 16:45:00, 滞后: 8.1分钟, 模式: 实时
[1h ] 数据时间: 16:00:00, 滞后: 53.0分钟, 模式: 滞后
时间错位: 52.0分钟
```

### 测试3: 对比回测

运行以下配置的回测并对比：

1. **baseline**: `mode: 'backtest'`（全部使用 `iloc[-2]`）
2. **live_safe**: 短周期实时，长周期滞后
3. **live_aggressive**: 全部使用实时

对比指标：
- 夏普比率
- 最大回撤
- 胜率
- 平均持仓时长

---

## 📊 预期效果

### 配置前（当前系统）

| 周期 | 索引 | 典型滞后 |
|------|------|---------|
| 5m   | -2   | 6-10分钟 |
| 15m  | -2   | 20-30分钟 |
| 1h   | -2   | 90-120分钟 |

**时间错位**: 100-120分钟

### 配置后（live_safe模式）

| 周期 | 索引 | 典型滞后 |
|------|------|---------|
| 5m   | -1   | 0-5分钟 ✅ |
| 15m  | -1   | 0-15分钟 ✅ |
| 1h   | -2   | 60-120分钟 |

**时间错位**: 60-120分钟（改善约40%）

---

## ⚠️ 注意事项

### 1. 实时K线的波动性

使用 `iloc[-1]` 时，K线未完成，数据会变化：

```python
# 16:52时的5m K线（16:50-16:55）
df.iloc[-1]['close']  # = 88120（当前价格）

# 16:53时重新获取
df.iloc[-1]['close']  # = 88135（价格变化了！）
```

**风险**: 可能出现"信号闪烁"（频繁切换买卖）

**缓解措施**:
- 设置 `min_completion_pct`（如30%），避免K线刚开始就使用
- 增加信号确认机制（连续N次出现）
- 设置最小持仓时间

### 2. 回测与实盘的差异

回测时必须使用 `mode: 'backtest'`，否则会产生未来函数：

```yaml
# 回测配置
mode: 'backtest'  # 强制使用 iloc[-2]
```

### 3. 不同策略的适配性

| 策略类型 | 推荐模式 | 原因 |
|---------|---------|------|
| 趋势跟随 | backtest/live_safe | 对滞后不敏感 |
| 突破交易 | live_safe/live_aggressive | 需要快速响应 |
| 反转交易 | live_aggressive | 时机敏感 |
| 套利策略 | live_aggressive | 需要极低延迟 |

---

## 🔧 故障排查

### 问题1: 配置文件未生效

**症状**: 日志中仍显示"模式: 滞后"且滞后时间很高

**检查**:
1. 确认 `config/data_alignment.yaml` 存在
2. 检查 YAML 语法是否正确（注意缩进）
3. 确认 `DataAlignmentHelper` 被正确初始化

**调试**:
```python
helper = DataAlignmentHelper()
print(f"加载的配置: {helper.config}")
print(f"当前模式: {helper.mode}")
```

### 问题2: 滞后告警过多

**症状**: 日志中频繁出现滞后告警

**解决**:
1. 调高 `lag_warning_threshold`
2. 检查网络延迟
3. 考虑使用更快的数据源

### 问题3: 信号闪烁

**症状**: 频繁产生相互矛盾的信号

**解决**:
1. 提高 `min_completion_pct`（如从30%调到50%）
2. 在策略中增加信号确认逻辑
3. 考虑切换回 `live_safe` 模式

---

## 📚 相关文档

- `DATA_FLOW_STRUCTURED.md` - 完整架构说明
- `config/data_alignment.yaml` - 配置模板
- `diagnose_data_lag.py` - 诊断工具
- `DIAGNOSIS_SUMMARY.md` - 问题诊断总结
- `src/utils/data_alignment.py` - 工具模块API文档

---

## 🚀 快速开始（TL;DR）

```bash
# 1. 运行诊断
python diagnose_data_lag.py

# 2. 编辑配置
vim config/data_alignment.yaml  # 设置 mode: 'live_safe'

# 3. 修改代码（仅需修改 builder.py）
# from src.utils.data_alignment import DataAlignmentHelper
# self.alignment_helper = DataAlignmentHelper()
# latest, metadata = self.alignment_helper.get_aligned_candle(df, timeframe)

# 4. 纸面测试
python run_live_trading.py --mode paper

# 5. 观察日志，确认滞后改善
```

---

**最后更新**: 2025-12-18  
**状态**: 就绪，可集成
