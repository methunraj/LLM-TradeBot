# 🤖 AI 量化交易系统

基于 LLM (DeepSeek) 的智能量化交易系统,支持多时间框架数据分析、技术指标计算、特征工程和自动化交易决策。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
# 复制环境变量模板
cp .env.example .env

# 设置 API 密钥
./set_api_keys.sh
```

### 3. 配置交易参数
```bash
# 复制配置文件模板
cp config.example.yaml config.yaml

# 编辑配置文件
vim config.yaml
```

### 4. 运行实盘交易
```bash
python run_live_trading.py
```

---

## 📁 项目结构

```
ai_trader/
├── src/                    # 核心源代码
│   ├── api/               # Binance API 客户端
│   ├── execution/         # 交易执行引擎
│   ├── features/          # 特征工程模块
│   ├── monitoring/        # 监控和日志
│   ├── risk/              # 风险管理
│   ├── strategy/          # LLM 决策引擎
│   └── utils/             # 工具函数
│
├── tests/                 # 单元测试
├── config/                # 配置文件
├── docs_organized/        # 项目文档 (157 个文件)
├── research/              # 研究和回测
├── data/                  # 数据存储
├── logs/                  # 日志文件
│
├── main.py                # 主程序入口
├── run_live_trading.py    # 实盘交易脚本
└── requirements.txt       # Python 依赖
```

---

## 🎯 核心功能

### 数据处理管道
- **Step 1**: K线数据获取 (多时间框架: 5m, 15m, 1h, 4h, 1d)
- **Step 2**: 技术指标计算 (MACD, RSI, Bollinger Bands, ATR, OBV 等)
- **Step 3**: 特征工程 (数据归一化、特征组合)
- **Step 4**: 数据质量检查
- **Step 5**: LLM 提示生成
- **Step 6**: LLM 智能决策
- **Step 7**: 交易信号输出

### 技术特性
- ✅ 多时间框架数据对齐
- ✅ 完整的技术指标库
- ✅ LLM 驱动的智能决策
- ✅ 风险管理和仓位控制
- ✅ 完整的数据归档 (Parquet + Stats)
- ✅ 详细的日志系统
- ✅ 实时交易执行

### 支持的交易对
- BTCUSDT (主要)
- 可扩展到其他币安合约交易对

---

## 📚 文档

### 入门文档
- [快速开始指南](docs_organized/01_快速开始/QUICK_START.md)
- [配置指南](docs_organized/02_配置指南/CONFIG_GUIDE.md)
- [系统架构](docs_organized/03_架构设计/ARCHITECTURE.md)

### 实盘交易
- [实盘交易快速开始](docs_organized/07_实盘交易/LIVE_TRADING_QUICKSTART.md)
- [实盘交易安全指南](docs_organized/07_实盘交易/LIVE_TRADING_SAFETY_GUIDE.md)
- [止盈止损指南](docs_organized/07_实盘交易/STOP_LOSS_TAKE_PROFIT_GUIDE.md)

### 完整文档
- [文档导航](DOCS_README.md) - 所有文档的导航指南
- [完整文档索引](docs_organized/README.md) - 157 个文档的详细索引
- [文档分类摘要](docs_organized/SUMMARY.md) - 按分类查看文档

---

## 🔧 技术栈

### 核心依赖
- **Python**: 3.11+
- **Binance API**: 币安合约交易
- **DeepSeek API**: LLM 决策引擎
- **pandas**: 数据处理
- **numpy**: 数值计算
- **ta-lib**: 技术指标
- **pyarrow**: 数据存储

### 技术指标
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Bollinger Bands
- ATR (Average True Range)
- OBV (On-Balance Volume)
- EMA/SMA (Exponential/Simple Moving Average)

---

## ⚙️ 配置说明

### 环境变量 (.env)
```bash
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_key

# 交易模式
TRADING_MODE=testnet  # 或 production
```

### 配置文件 (config.yaml)
```yaml
trading:
  symbol: BTCUSDT
  timeframe: 5m
  leverage: 1
  risk_per_trade: 0.01

strategy:
  model: deepseek-chat
  temperature: 0.1
  max_tokens: 500

risk:
  max_position_size: 1000
  stop_loss_pct: 0.02
  take_profit_pct: 0.04
```

---

## 🔒 安全提示

⚠️ **重要安全措施**:

1. **API 密钥**: 妥善保管,不要提交到版本控制
2. **测试网先行**: 先在测试网测试,确认无误后再上生产
3. **风险控制**: 设置合理的止损和仓位大小
4. **监控系统**: 密切监控交易日志和账户状态
5. **IP 白名单**: 建议为 API 密钥设置 IP 白名单

---

## 📊 数据归档

系统自动归档所有步骤的数据:

```
data/
├── step1/                 # K线数据 (Parquet + Stats)
├── step2/                 # 技术指标 (Parquet + Stats)
├── step3/                 # 特征数据 (Parquet + Stats)
├── step4/                 # 质量检查 (JSON)
├── step5/                 # LLM 提示 (TXT)
├── step6/                 # LLM 决策 (JSON)
└── step7/                 # 交易信号 (JSON)
```

每个步骤都包含:
- **Parquet 文件**: 高效的数据存储
- **Stats 文件**: 数据统计信息
- **时间戳**: 完整的审计跟踪

---

## 📈 系统监控

### 日志系统
```bash
# 查看实时日志
tail -f logs/live_trading_YYYYMMDD.log

# 查看数据流日志
tail -f logs/data_flow_YYYYMMDD.log

# 查看交易日志
tail -f logs/trade_YYYYMMDD.json
```

### 性能指标
- 数据获取延迟
- 指标计算时间
- LLM 响应时间
- 交易执行时间

---

## 🧪 测试

```bash
# 运行单元测试
python -m pytest tests/

# 测试特定模块
python -m pytest tests/test_step3_features.py
```

---

## 🛠️ 维护工具

### 文档管理
```bash
# 整理文档
python organize_docs.py
```

### 项目清理
```bash
# 预览清理
python cleanup_project.py

# 执行清理
python cleanup_project.py --execute
```

---

## 📝 开发指南

### 添加新策略
1. 在 `src/strategy/` 创建新策略类
2. 继承基础策略接口
3. 实现决策逻辑
4. 在配置文件中启用

### 添加新指标
1. 在 `src/features/technical_features.py` 添加指标计算
2. 更新特征构建器
3. 在 Step 2 中注册新指标

### 添加新交易对
1. 在 `config.yaml` 中添加交易对配置
2. 确认币安支持该交易对
3. 测试数据获取和交易执行

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

---

## 📄 许可证

MIT License

---

## 📞 支持

- 📚 [完整文档](docs_organized/README.md)
- 🐛 [问题诊断](docs_organized/12_其他/DIAGNOSIS_SUMMARY.md)
- 📊 [项目状态](docs_organized/12_其他/PROJECT_STATUS_OVERVIEW.md)

---

## 🎉 最新更新

**2024-12-19**:
- ✅ 完成项目清理,移除 71 个临时文件
- ✅ 整理 157 个文档到 docs_organized/
- ✅ 修复 Step2/3 数据归档问题
- ✅ 验证所有步骤的数据流
- ✅ 系统已就绪,可用于实盘交易

---

**从零到一,从混沌到秩序,开启智能交易新纪元!** 🚀
