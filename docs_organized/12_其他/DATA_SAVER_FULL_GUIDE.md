# DataSaver 完整功能快速指南

## 📖 概述

DataSaver 现已支持完整的 9 个步骤数据归档，覆盖从原始数据到实时交易的整个交易流程。

## 📁 完整目录结构

```
data/
  ├── step1/YYYYMMDD/    # 原始K线数据
  ├── step2/YYYYMMDD/    # 技术指标数据
  ├── step3/YYYYMMDD/    # 特征快照数据
  ├── step4/YYYYMMDD/    # 多周期上下文数据  🆕
  ├── step5/YYYYMMDD/    # Markdown格式化文本 🆕
  ├── step6/YYYYMMDD/    # LLM决策输出       🆕
  ├── step7/YYYYMMDD/    # 交易执行记录      🆕
  ├── step8/YYYYMMDD/    # 回测/绩效数据     🆕
  └── step9/YYYYMMDD/    # 实时交易事件      🆕
```

## 🚀 快速上手（完整流程）

### 初始化

```python
from src.utils.data_saver import DataSaver

saver = DataSaver()
```

### 步骤1-3（已有功能）

```python
# 步骤1: 保存原始K线
saved = saver.save_step1_klines(klines, 'BTCUSDT', '5m')

# 步骤2: 保存技术指标
saved = saver.save_step2_indicators(df, 'BTCUSDT', '5m', snapshot_id)

# 步骤3: 保存特征快照
saved = saver.save_step3_features(features_df, 'BTCUSDT', '5m', snapshot_id, 'v1')
```

### 步骤4: 保存多周期上下文 🆕

```python
# 多周期市场数据整合
context = {
    'market_overview': {
        'symbol': 'BTCUSDT',
        'current_price': 50000.0,
        'trend': 'bullish'
    },
    'timeframes': {
        '5m': {'rsi': 65.5, 'macd': 0.02},
        '15m': {'rsi': 58.3, 'macd': 0.01},
        '1h': {'rsi': 52.1, 'macd': -0.005}
    },
    'signals': {
        'buy_signals': 2,
        'sell_signals': 1
    }
}

saved = saver.save_step4_context(
    context=context,
    symbol='BTCUSDT',
    timeframe='5m',
    snapshot_id=snapshot_id
)
# 返回: {'json': 'data/step4/.../step4_context_*.json'}
```

### 步骤5: 保存Markdown格式化文本 🆕

```python
# LLM输入文本（Markdown格式）
markdown_text = """## 市场快照
**交易对**: BTCUSDT
**当前价格**: 50,000.00 USDT

### 技术指标 (5分钟)
- **RSI**: 65.5 (偏买方)
- **MACD**: 0.02% (金叉)

### 交易建议
建议采取谨慎乐观策略...
"""

saved = saver.save_step5_markdown(
    markdown_text=markdown_text,
    symbol='BTCUSDT',
    timeframe='5m',
    snapshot_id=snapshot_id
)
# 返回: {'md': '.../*.md', 'stats': '.../*_stats.txt'}
```

**统计报告包含**：
- 总字符数、行数、字节数
- 内容预览（前500字符）

### 步骤6: 保存LLM决策输出 🆕

```python
# LLM决策结果
decision = {
    'action': 'buy',               # 决策动作
    'confidence': 75,              # 信心度
    'reason': '市场呈现明显上涨趋势...',
    'suggested_quantity': 0.1,
    'stop_loss': 49500.0,
    'take_profit': 51000.0,
    'risk_level': 'medium'
}

saved = saver.save_step6_decision(
    decision=decision,
    symbol='BTCUSDT',
    timeframe='5m',
    snapshot_id=snapshot_id
)
# 返回: {'json': '.../*.json', 'stats': '.../*_stats.txt'}
```

**统计报告包含**：
- 决策动作、信心度、原因
- 完整决策数据JSON

### 步骤7: 保存交易执行记录 🆕

```python
# 实际交易执行记录
execution_record = {
    'order_id': 'ORD_20251217_001',
    'symbol': 'BTCUSDT',
    'action': 'buy',
    'quantity': 0.1,
    'price': 50000.0,
    'total_value': 5000.0,
    'fee': 5.0,
    'status': 'filled',
    'filled_time': datetime.now().isoformat()
}

saved = saver.save_step7_execution(
    execution_record=execution_record,
    symbol='BTCUSDT',
    timeframe='5m',
    order_id=execution_record['order_id']
)
# 返回: {'json': '.../*.json', 'csv': '.../step7_executions_*.csv'}
```

**特点**：
- 每个订单单独JSON文件
- 所有订单追加到CSV文件（方便统计分析）

### 步骤8: 保存回测/绩效数据 🆕

```python
# 回测结果
backtest_results = {
    'metrics': {
        'total_return': 15.5,      # 总收益率
        'sharpe_ratio': 1.8,       # 夏普比率
        'max_drawdown': -8.2,      # 最大回撤
        'win_rate': 62.5,          # 胜率
        'total_trades': 100        # 总交易次数
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
        # ... 更多交易记录
    ]
}

saved = saver.save_step8_backtest(
    backtest_results=backtest_results,
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='20251201',
    end_date='20251217',
    strategy_version='v1'
)
# 返回: {
#   'json': '.../*.json',
#   'stats': '.../*_performance.txt',
#   'trades_csv': '.../*_trades.csv',
#   'trades_parquet': '.../*_trades.parquet'
# }
```

**统计报告包含**：
- 关键绩效指标（收益率、夏普、回撤、胜率）
- 完整回测数据预览
- 交易记录保存为CSV和Parquet（高效分析）

### 步骤9: 保存实时交易事件 🆕

```python
# 实时交易事件（每次成功下单后自动归档）
trade_event = {
    'trade_id': 'ORDER_123456',
    'timestamp': datetime.now().isoformat(),
    'signal': 'BUY',
    'price': 50000.0,
    'quantity': 0.1,
    'amount': 5000.0,
    'order_id': 'ORDER_123456',
    'success': True,
    'decision': {
        'action': 'open_long',
        'leverage': 1,
        'stop_loss_pct': 1.0,
        'take_profit_pct': 2.0
    },
    'execution_result': {
        'order_id': 'ORDER_123456',
        'filled_qty': 0.1,
        'avg_price': 50000.0
    },
    'market_state_snapshot': {
        'current_price': 50000.0,
        'timeframes': {
            '5m': {'rsi': 65.5, 'trend': 'uptrend'},
            '15m': {'rsi': 58.3, 'trend': 'uptrend'}
        }
    },
    'account_info': {
        'available_balance': 10000.0
    }
}

saved = saver.save_step9_trade_event(
    trade_event=trade_event,
    symbol='BTCUSDT',
    timeframe='5m',
    trade_id='ORDER_123456'
)
# 返回: {
#   'json': 'data/step9/.../step9_trade_*.json',
#   'csv': 'data/step9/.../step9_trades_*.csv',
#   'parquet': 'data/step9/.../step9_trades_*.parquet'
# }
```

**特点**：
- 每次交易单独保存为JSON
- 自动追加到当日CSV和Parquet汇总文件
- 包含完整的决策、执行、市场状态快照
- 支持实时分析和历史回溯

## 📊 数据流程对应关系

```
┌─────────────────────────────────────────────────────────────┐
│ 完整的AI量化交易数据流程                                     │
└─────────────────────────────────────────────────────────────┘

Step1: 获取K线数据
   ↓ (原始OHLCV)
   data/step1/YYYYMMDD/*.parquet

Step2: 计算技术指标
   ↓ (RSI, MACD, ATR, BB...)
   data/step2/YYYYMMDD/*.parquet

Step3: 提取特征快照
   ↓ (归一化特征)
   data/step3/YYYYMMDD/*.parquet

Step4: 构建多周期上下文 🆕
   ↓ (5m/15m/1h整合)
   data/step4/YYYYMMDD/*.json

Step5: 格式化Markdown文本 🆕
   ↓ (LLM输入)
   data/step5/YYYYMMDD/*.md

Step6: LLM决策分析 🆕
   ↓ (buy/sell/hold + 信心度)
   data/step6/YYYYMMDD/*.json

Step7: 执行交易 🆕
   ↓ (订单记录)
   data/step7/YYYYMMDD/*.json + *.csv

Step8: 回测分析 🆕
   ↓ (绩效评估)
   data/step8/YYYYMMDD/*.json + *_trades.parquet

Step9: 实时交易事件 🆕
   ↓ (每次下单记录)
   data/step9/YYYYMMDD/*.json + *.csv + *.parquet
```

## 🔍 文件管理

### 列出所有步骤的文件

```python
# 列出特定步骤
for step in ['step4', 'step5', 'step6', 'step7', 'step8', 'step9']:
    files = saver.list_files(step=step)
    print(f"{step}: {len(files)} 个文件")

# 列出所有JSON文件
all_json = saver.list_files(pattern='.json')

# 列出所有统计报告
all_stats = saver.list_files(pattern='stats')
```

### 清理旧数据（所有8个步骤）

```python
deleted = saver.cleanup_old_data(days_to_keep=7)
print(f"已清理: {deleted}")
# 输出: {'step1': 0, 'step2': 0, ..., 'step8': 0}
```

## 📈 使用场景

### 场景1: 实盘交易流程

```python
# 1. 获取K线
klines = fetch_klines()
saver.save_step1_klines(klines, 'BTCUSDT', '5m')

# 2. 计算指标
df = calculate_indicators(klines)
saver.save_step2_indicators(df, 'BTCUSDT', '5m', snapshot_id)

# 3. 提取特征
features = extract_features(df)
saver.save_step3_features(features, 'BTCUSDT', '5m', snapshot_id, 'v1')

# 4. 构建上下文
context = build_context(features)
saver.save_step4_context(context, 'BTCUSDT', '5m', snapshot_id)

# 5. 准备LLM输入
markdown = format_to_markdown(context)
saver.save_step5_markdown(markdown, 'BTCUSDT', '5m', snapshot_id)

# 6. 获取LLM决策
decision = get_llm_decision(markdown)
saver.save_step6_decision(decision, 'BTCUSDT', '5m', snapshot_id)

# 7. 执行交易（如果决策是buy/sell）
if decision['action'] in ['buy', 'sell']:
    execution = execute_trade(decision)
    saver.save_step7_execution(execution, 'BTCUSDT', '5m')
```

### 场景2: 回测分析

```python
# 运行回测
results = run_backtest(
    symbol='BTCUSDT',
    timeframe='5m',
    start='20251201',
    end='20251217'
)

# 保存回测结果
saver.save_step8_backtest(
    results,
    'BTCUSDT',
    '5m',
    '20251201',
    '20251217',
    'v1'
)

# 读取绩效报告
with open(saved['stats'], 'r') as f:
    print(f.read())
```

### 场景3: 数据分析

```python
import pandas as pd

# 分析所有交易执行记录
exec_csv = 'data/step7/20251217/step7_executions_BTCUSDT_5m.csv'
df = pd.read_csv(exec_csv)

print(f"总交易次数: {len(df)}")
print(f"买入次数: {(df['action'] == 'buy').sum()}")
print(f"卖出次数: {(df['action'] == 'sell').sum()}")

# 分析回测交易记录
trades_file = 'data/step8/.../step8_trades_*.parquet'
trades = pd.read_parquet(trades_file)
print(f"平均盈利: {trades['profit'].mean()}")
print(f"最大盈利: {trades['profit'].max()}")
```

## 📝 文件格式对比

| 步骤 | 主要格式 | 辅助格式 | 推荐场景 |
|------|----------|----------|----------|
| Step1 | Parquet | JSON, CSV | 原始数据存储 |
| Step2 | Parquet | Stats TXT | 技术指标存储 |
| Step3 | Parquet | Stats TXT | 特征数据存储 |
| Step4 | JSON | - | 上下文数据（层级结构） |
| Step5 | Markdown | Stats TXT | LLM输入文本 |
| Step6 | JSON | Stats TXT | 决策结果存储 |
| Step7 | JSON + CSV | - | 订单记录（JSON明细+CSV汇总） |
| Step8 | JSON + Parquet | Stats TXT + CSV | 回测结果（JSON汇总+Parquet交易明细） |
| Step9 | JSON + CSV + Parquet | - | 实时交易事件（JSON明细+CSV/Parquet汇总） |

## ⚡ 性能优化建议

### 生产环境

```python
# 1. 仅保存必要格式
saver.save_step1_klines(klines, 'BTCUSDT', '5m', save_formats=['parquet'])

# 2. 关闭统计报告（步骤2-3可选）
saver.save_step2_indicators(df, 'BTCUSDT', '5m', snapshot_id, save_stats=False)

# 3. 定期清理（每天凌晨执行）
saver.cleanup_old_data(days_to_keep=7)
```

### 调试环境

```python
# 保存所有格式和统计报告
saver.save_step1_klines(klines, 'BTCUSDT', '5m', save_formats=['json', 'csv', 'parquet'])
saver.save_step2_indicators(df, 'BTCUSDT', '5m', snapshot_id, save_stats=True)
saver.save_step5_markdown(markdown, 'BTCUSDT', '5m', snapshot_id)  # 自动生成stats
```

## 🧪 测试

```bash
# 测试步骤1-3
python test_data_saver.py

# 测试步骤4-8 🆕
python test_data_saver_extended.py

# 验证所有步骤
python verify_data_saver.py
```

## 📚 文档参考

- [完整使用文档](DATA_SAVER_USAGE.md) - API参考和最佳实践
- [重构总结](DATA_SAVER_REFACTOR_SUMMARY.md) - 实现细节
- [README](DATA_SAVER_README.md) - 总览

---

🎉 **现在你可以管理完整的AI量化交易数据流程了！** 🚀
