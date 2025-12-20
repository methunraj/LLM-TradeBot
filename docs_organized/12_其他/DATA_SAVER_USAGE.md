# DataSaver 工具类使用文档

## 概述

`DataSaver` 是一个用于组织和管理 AI 量化交易系统数据文件的工具类，支持按步骤和日期自动归档数据。

## 目录结构

```
data/
  ├── step1/              # 步骤1：原始K线数据
  │   └── 20251217/
  │       ├── step1_klines_BTCUSDT_5m_20251217_220226.json
  │       ├── step1_klines_BTCUSDT_5m_20251217_220226.csv
  │       ├── step1_klines_BTCUSDT_5m_20251217_220226.parquet
  │       └── step1_stats_BTCUSDT_5m_20251217_220226.txt
  │
  ├── step2/              # 步骤2：技术指标数据
  │   └── 20251217/
  │       ├── step2_indicators_BTCUSDT_5m_20251217_220226_snap_xxx.parquet
  │       └── step2_stats_BTCUSDT_5m_20251217_220226_snap_xxx.txt
  │
  └── step3/              # 步骤3：特征快照数据
      └── 20251217/
          ├── step3_features_BTCUSDT_5m_20251217_220226_v1.parquet
          └── step3_stats_BTCUSDT_5m_20251217_220226_v1.txt
```

## 功能特性

### 1. 自动按日期归档
- 所有数据文件自动按日期（YYYYMMDD）组织
- 默认使用当前日期，也可指定日期
- 自动创建目录结构

### 2. 多格式支持
- **步骤1（原始K线）**：支持 JSON、CSV、Parquet 三种格式
- **步骤2（技术指标）**：Parquet 格式（高效存储）
- **步骤3（特征快照）**：Parquet 格式（高效存储）
- **统计报告**：TXT 格式（人类可读）

### 3. 自动生成统计报告
- 数据质量检查（缺失值、无穷值、重复值）
- 关键指标统计（均值、标准差、分位数）
- 预热期标记统计
- 有效特征率统计
- 时间缺口检测统计

### 4. 文件管理功能
- 列出指定步骤和日期的所有文件
- 按模式过滤文件
- 清理超过指定天数的旧数据

## 使用示例

### 基本初始化

```python
from src.utils.data_saver import DataSaver

# 创建实例（使用默认 data/ 目录）
saver = DataSaver()

# 或指定自定义目录
saver = DataSaver(base_dir='custom_data')
```

### 步骤1：保存原始K线数据

```python
# 获取K线数据（示例）
klines = [
    {
        'timestamp': 1734451200000,
        'open': 50000.0,
        'high': 50100.0,
        'low': 49900.0,
        'close': 50050.0,
        'volume': 10.5
    },
    # ... 更多K线
]

# 保存K线数据（支持多种格式）
saved_files = saver.save_step1_klines(
    klines=klines,
    symbol='BTCUSDT',
    timeframe='5m',
    save_formats=['json', 'csv', 'parquet']  # 可选格式
)

# 返回值示例：
# {
#     'json': 'data/step1/20251217/step1_klines_BTCUSDT_5m_20251217_220226.json',
#     'csv': 'data/step1/20251217/step1_klines_BTCUSDT_5m_20251217_220226.csv',
#     'parquet': 'data/step1/20251217/step1_klines_BTCUSDT_5m_20251217_220226.parquet',
#     'stats': 'data/step1/20251217/step1_stats_BTCUSDT_5m_20251217_220226.txt'
# }
```

### 步骤2：保存技术指标数据

```python
import pandas as pd

# 假设已经计算好技术指标的 DataFrame
indicators_df = pd.DataFrame({
    'timestamp': [...],
    'open': [...],
    'close': [...],
    'rsi': [...],
    'macd': [...],
    'atr': [...],
    'is_warmup': [...]  # 预热期标记
})

# 保存技术指标
snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
saved_files = saver.save_step2_indicators(
    df=indicators_df,
    symbol='BTCUSDT',
    timeframe='5m',
    snapshot_id=snapshot_id,
    save_stats=True  # 是否生成统计报告
)

# 返回值示例：
# {
#     'parquet': 'data/step2/20251217/step2_indicators_BTCUSDT_5m_20251217_220226_snap_xxx.parquet',
#     'stats': 'data/step2/20251217/step2_stats_BTCUSDT_5m_20251217_220226_snap_xxx.txt'
# }
```

### 步骤3：保存特征快照数据

```python
# 假设已经提取好特征的 DataFrame
features_df = pd.DataFrame({
    'timestamp': [...],
    'rsi_norm': [...],
    'macd_pct': [...],
    'atr_pct': [...],
    'is_feature_valid': [...],  # 特征有效性标记
    'has_time_gap': [...],      # 时间缺口标记
    'feature_version': 'v1'     # 特征版本
})

# 保存特征快照
saved_files = saver.save_step3_features(
    features=features_df,
    symbol='BTCUSDT',
    timeframe='5m',
    source_snapshot_id='snap_xxx',
    feature_version='v1',
    save_stats=True  # 是否生成统计报告
)

# 返回值示例：
# {
#     'parquet': 'data/step3/20251217/step3_features_BTCUSDT_5m_20251217_220226_v1.parquet',
#     'stats': 'data/step3/20251217/step3_stats_BTCUSDT_5m_20251217_220226_v1.txt'
# }
```

### 文件管理功能

```python
# 列出所有步骤1的文件
step1_files = saver.list_files(step='step1')

# 列出特定日期的所有文件
files_20251217 = saver.list_files(step='step1', date='20251217')

# 列出所有统计报告
stats_files = saver.list_files(pattern='stats')

# 列出所有步骤的文件（不指定 step）
all_files = saver.list_files()

# 清理超过7天的旧数据
deleted = saver.cleanup_old_data(days_to_keep=7)
# 返回值示例: {'step1': 3, 'step2': 2, 'step3': 2}
```

## 统计报告内容

### 步骤1统计报告

```
================================================================================
步骤1 原始K线数据统计报告
================================================================================

交易对: BTCUSDT
时间周期: 5m
数据量: 100 根K线
时间范围: 2025-12-17 14:00:00 ~ 2025-12-17 22:15:00
获取时间: 20251217_220226

价格统计:
  开盘价: ...
  收盘价: ...

成交量统计:
  ...

数据完整性:
  缺失值: 0
  重复行: 0

文件清单:
  JSON: step1_klines_BTCUSDT_5m_20251217_220226.json (33.4 KB)
  CSV: step1_klines_BTCUSDT_5m_20251217_220226.csv (13.6 KB)
  PARQUET: step1_klines_BTCUSDT_5m_20251217_220226.parquet (17.2 KB)
```

### 步骤2统计报告

```
================================================================================
步骤2 技术指标统计报告
================================================================================

交易对: BTCUSDT
时间周期: 5m
快照ID: snap_20251217_221106
数据量: 100 根K线
生成时间: 20251217_221106

数据质量:
  总列数: 19
  缺失值总数: 20
  无穷值总数: 0
  预热期数据: 26 根 (26.0%)

关键技术指标统计:

  rsi:
    有效值: 100/100 (100.0%)
    均值: 51.622518
    标准差: 12.047345
    最小值: 30.718069
    最大值: 69.596451

  macd:
    有效值: 100/100 (100.0%)
    均值: 0.000450
    标准差: 0.009945
    ...
```

### 步骤3统计报告

```
================================================================================
步骤3 特征快照统计报告
================================================================================

交易对: BTCUSDT
时间周期: 5m
特征版本: v1
数据量: 100 根K线
生成时间: 20251217_221106

数据质量:
  总特征数: 27
  缺失值总数: 22
  无穷值总数: 0
  有效特征行: 74/100 (74.0%)
  时间缺口: 5 处 (5.0%)

特征列表:
  - atr
  - atr_pct
  - macd_pct
  - rsi_norm
  - is_feature_valid
  - has_time_gap
  ...

数值特征统计:

  rsi_norm:
    有效值: 100/100 (100.0%)
    均值: 0.032450
    标准差: 0.240947
    分位数 [5%, 25%, 50%, 75%, 95%]: [-0.314172, -0.167881, 0.015983, 0.280263, 0.370380]
```

## 最佳实践

### 1. 命名规范
- 文件名包含：步骤、交易对、时间周期、时间戳、版本/快照ID
- 统一格式：`step{N}_{type}_{symbol}_{timeframe}_{timestamp}_{id}.{ext}`

### 2. 数据完整性
- 每次保存都生成统计报告（`save_stats=True`）
- 定期检查缺失值、无穷值
- 监控预热期和有效特征率

### 3. 存储管理
- 定期清理旧数据（`cleanup_old_data`）
- 生产环境建议保留 7-30 天
- 重要数据归档到长期存储

### 4. 性能优化
- 优先使用 Parquet 格式（压缩率高、读取快）
- 大规模数据避免使用 JSON（体积大）
- 统计报告仅在需要时生成

## 文件格式对比

| 格式 | 大小 | 读取速度 | 兼容性 | 推荐场景 |
|------|------|----------|--------|----------|
| JSON | 大 | 慢 | 高 | 调试、人工检查 |
| CSV | 中 | 中 | 高 | Excel查看、跨平台 |
| Parquet | 小 | 快 | 中 | 生产环境、大数据 |
| TXT | 小 | - | 最高 | 统计报告、日志 |

## 故障排查

### 问题1：目录权限错误
```python
# 确保有写权限
import os
os.makedirs('data/step1/20251217', exist_ok=True)
```

### 问题2：数据格式不匹配
```python
# 确保 DataFrame 包含必要字段
required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
assert all(col in df.columns for col in required_cols)
```

### 问题3：磁盘空间不足
```python
# 定期清理旧数据
saver.cleanup_old_data(days_to_keep=7)
```

## 迁移旧数据

如果你有旧的目录结构（`data/YYYYMMDD/`），可以使用迁移脚本：

```bash
python migrate_data_structure.py
```

迁移后：
- `data/20251217/` → `data/step1/20251217/`
- 所有文件自动移动到新结构
- 旧文件夹自动删除

## 测试

运行完整测试：

```bash
python test_data_saver.py
```

测试覆盖：
- ✅ 步骤1保存（JSON/CSV/Parquet）
- ✅ 步骤2保存（指标+统计报告）
- ✅ 步骤3保存（特征+统计报告）
- ✅ 文件列表功能
- ✅ 清理旧数据功能

## 注意事项

1. **时间戳格式**：所有时间戳使用毫秒级Unix时间戳
2. **特征版本**：建议使用语义化版本（v1, v2, v1.1等）
3. **快照ID**：使用时间戳确保唯一性
4. **数据质量**：保存前检查 NaN、inf 值
5. **备份策略**：重要数据定期备份到云存储

## API 参考

### DataSaver 类

#### `__init__(base_dir='data')`
初始化 DataSaver 实例。

**参数：**
- `base_dir` (str): 数据根目录，默认 'data'

#### `save_step1_klines(klines, symbol, timeframe, save_formats=['json', 'csv', 'parquet'])`
保存步骤1的原始K线数据。

**参数：**
- `klines` (List[Dict]): K线数据列表
- `symbol` (str): 交易对，如 'BTCUSDT'
- `timeframe` (str): 时间周期，如 '5m'
- `save_formats` (List[str]): 保存格式列表

**返回：**
- `Dict[str, str]`: 保存的文件路径字典

#### `save_step2_indicators(df, symbol, timeframe, snapshot_id, save_stats=True)`
保存步骤2的技术指标数据。

**参数：**
- `df` (pd.DataFrame): 包含技术指标的DataFrame
- `symbol` (str): 交易对
- `timeframe` (str): 时间周期
- `snapshot_id` (str): 快照ID
- `save_stats` (bool): 是否保存统计报告

**返回：**
- `Dict[str, str]`: 保存的文件路径字典

#### `save_step3_features(features, symbol, timeframe, source_snapshot_id, feature_version='v1', save_stats=True)`
保存步骤3的特征快照数据。

**参数：**
- `features` (pd.DataFrame): 特征DataFrame
- `symbol` (str): 交易对
- `timeframe` (str): 时间周期
- `source_snapshot_id` (str): 来源快照ID
- `feature_version` (str): 特征版本
- `save_stats` (bool): 是否保存统计报告

**返回：**
- `Dict[str, str]`: 保存的文件路径字典

#### `list_files(step=None, date=None, pattern=None)`
列出指定步骤和日期的所有文件。

**参数：**
- `step` (str, optional): 步骤名称 'step1'/'step2'/'step3'
- `date` (str, optional): 日期字符串 YYYYMMDD
- `pattern` (str, optional): 文件名模式

**返回：**
- `List[str]`: 文件路径列表

#### `cleanup_old_data(days_to_keep=7)`
清理超过指定天数的旧数据。

**参数：**
- `days_to_keep` (int): 保留最近N天的数据

**返回：**
- `Dict[str, int]`: 删除统计 {step: deleted_count}

## 更新日志

### v1.0.0 (2025-12-17)
- ✅ 实现按步骤和日期自动归档
- ✅ 支持多格式保存（JSON/CSV/Parquet）
- ✅ 自动生成统计报告
- ✅ 文件管理和清理功能
- ✅ 完整的单元测试
- ✅ 旧数据迁移工具

## 联系与支持

如有问题或建议，请提交 Issue 或 Pull Request。
