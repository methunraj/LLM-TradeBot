# DataSaver 快速开始指南

## 5分钟快速上手

### 第一步：导入模块

```python
from src.utils.data_saver import DataSaver

# 创建实例
saver = DataSaver()
```

### 第二步：保存原始K线数据（步骤1）

```python
# 假设你已经获取了K线数据
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

# 保存数据
saved_files = saver.save_step1_klines(
    klines=klines,
    symbol='BTCUSDT',
    timeframe='5m'
)

print(f"✅ 已保存到: {saved_files['parquet']}")
```

**输出示例：**
```
✅ 已保存到: data/step1/20251217/step1_klines_BTCUSDT_5m_20251217_220226.parquet
```

### 第三步：保存技术指标数据（步骤2）

```python
import pandas as pd

# 假设你已经计算了技术指标
indicators_df = pd.DataFrame({
    'timestamp': [...],
    'open': [...],
    'close': [...],
    'rsi': [...],
    'macd': [...],
    'atr': [...],
    # ... 更多指标
})

# 生成快照ID
from datetime import datetime
snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 保存数据
saved_files = saver.save_step2_indicators(
    df=indicators_df,
    symbol='BTCUSDT',
    timeframe='5m',
    snapshot_id=snapshot_id
)

print(f"✅ 已保存到: {saved_files['parquet']}")
print(f"📊 统计报告: {saved_files['stats']}")
```

### 第四步：保存特征快照（步骤3）

```python
# 假设你已经提取了特征
features_df = pd.DataFrame({
    'timestamp': [...],
    'rsi_norm': [...],
    'macd_pct': [...],
    'atr_pct': [...],
    # ... 更多特征
})

# 保存数据
saved_files = saver.save_step3_features(
    features=features_df,
    symbol='BTCUSDT',
    timeframe='5m',
    source_snapshot_id=snapshot_id,
    feature_version='v1'
)

print(f"✅ 已保存到: {saved_files['parquet']}")
print(f"📊 统计报告: {saved_files['stats']}")
```

### 第五步：查看统计报告

```python
# 读取统计报告
stats_file = saved_files['stats']
with open(stats_file, 'r') as f:
    print(f.read())
```

**输出示例：**
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
  - rsi_norm
  - macd_pct
  - atr_pct
  ...
```

## 常用操作

### 列出今天的所有文件

```python
# 列出步骤1的文件
step1_files = saver.list_files(step='step1')
for f in step1_files:
    print(f)

# 列出所有统计报告
stats_files = saver.list_files(pattern='stats')
for f in stats_files:
    print(f)
```

### 清理旧数据（保留7天）

```python
deleted = saver.cleanup_old_data(days_to_keep=7)
print(f"已清理: step1={deleted['step1']}, step2={deleted['step2']}, step3={deleted['step3']}")
```

### 读取保存的数据

```python
import pandas as pd

# 读取步骤1数据
df = pd.read_parquet('data/step1/20251217/step1_klines_BTCUSDT_5m_20251217_220226.parquet')
print(df.head())

# 读取步骤2数据
df = pd.read_parquet('data/step2/20251217/step2_indicators_BTCUSDT_5m_20251217_220226_snap_xxx.parquet')
print(df.columns)

# 读取步骤3数据
df = pd.read_parquet('data/step3/20251217/step3_features_BTCUSDT_5m_20251217_220226_v1.parquet')
print(df.describe())
```

## 完整示例

```python
from src.utils.data_saver import DataSaver
from datetime import datetime
import pandas as pd

def main():
    # 1. 初始化
    saver = DataSaver()
    
    # 2. 获取K线数据（这里是示例）
    klines = [...]  # 你的K线数据
    
    # 3. 保存步骤1
    print("📥 保存原始K线数据...")
    saved_step1 = saver.save_step1_klines(
        klines=klines,
        symbol='BTCUSDT',
        timeframe='5m',
        save_formats=['parquet']  # 生产环境推荐只用 parquet
    )
    print(f"✅ 步骤1完成: {saved_step1['parquet']}")
    
    # 4. 计算技术指标
    print("\n🔧 计算技术指标...")
    indicators_df = calculate_indicators(klines)  # 你的指标计算函数
    snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 5. 保存步骤2
    print("💾 保存技术指标...")
    saved_step2 = saver.save_step2_indicators(
        df=indicators_df,
        symbol='BTCUSDT',
        timeframe='5m',
        snapshot_id=snapshot_id,
        save_stats=True
    )
    print(f"✅ 步骤2完成: {saved_step2['parquet']}")
    print(f"📊 统计报告: {saved_step2['stats']}")
    
    # 6. 提取特征
    print("\n🎯 提取特征...")
    features_df = extract_features(indicators_df)  # 你的特征提取函数
    
    # 7. 保存步骤3
    print("💾 保存特征快照...")
    saved_step3 = saver.save_step3_features(
        features=features_df,
        symbol='BTCUSDT',
        timeframe='5m',
        source_snapshot_id=snapshot_id,
        feature_version='v1',
        save_stats=True
    )
    print(f"✅ 步骤3完成: {saved_step3['parquet']}")
    print(f"📊 统计报告: {saved_step3['stats']}")
    
    # 8. 查看统计
    print("\n📈 查看步骤3统计报告:")
    with open(saved_step3['stats'], 'r') as f:
        print(f.read()[:500])  # 显示前500字符
    
    print("\n🎉 所有步骤完成！")

if __name__ == '__main__':
    main()
```

## 测试运行

运行测试脚本验证功能：

```bash
# 测试 DataSaver 所有功能
python test_data_saver.py

# 迁移旧数据到新结构
python migrate_data_structure.py
```

## 目录结构说明

```
data/
  ├── step1/              # 步骤1：原始K线数据
  │   └── 20251217/       # 按日期归档
  │       ├── *.json      # JSON格式（调试用）
  │       ├── *.csv       # CSV格式（Excel查看）
  │       ├── *.parquet   # Parquet格式（生产环境）⭐
  │       └── *_stats.txt # 统计报告
  │
  ├── step2/              # 步骤2：技术指标数据
  │   └── 20251217/
  │       ├── *_indicators_*.parquet  # 指标数据
  │       └── *_stats_*.txt           # 统计报告
  │
  └── step3/              # 步骤3：特征快照数据
      └── 20251217/
          ├── *_features_*_v1.parquet # 特征数据
          └── *_stats_*_v1.txt        # 统计报告
```

## 注意事项

1. **时间戳格式**：使用毫秒级Unix时间戳
2. **文件格式**：生产环境推荐使用 Parquet（体积小、速度快）
3. **统计报告**：建议保留用于监控数据质量
4. **清理策略**：定期清理旧数据，生产环境建议保留7-30天
5. **快照ID**：使用时间戳确保唯一性

## 需要帮助？

查看完整文档：
- 📖 [使用文档](DATA_SAVER_USAGE.md) - 完整的功能说明和API参考
- 📝 [重构总结](DATA_SAVER_REFACTOR_SUMMARY.md) - 实现细节和优化建议

---

🎉 现在你已经掌握了 DataSaver 的基本使用！开始管理你的交易数据吧！
