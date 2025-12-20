# AI 量化交易系统 - 文档导航

> 📚 **所有项目文档已整理到 `docs_organized/` 目录**

## 🚀 快速导航

### 📖 开始使用
- **[完整文档索引](docs_organized/README.md)** - 所有文档的详细索引 (157 个文件)
- **[分类摘要](docs_organized/SUMMARY.md)** - 按分类查看文档
- **[快速开始](docs_organized/01_快速开始/)** - 项目入门指南

### 🎯 常用文档

#### 新手入门
- [快速开始指南](docs_organized/01_快速开始/QUICK_START.md)
- [配置指南](docs_organized/02_配置指南/CONFIG_GUIDE.md)
- [系统架构](docs_organized/03_架构设计/ARCHITECTURE.md)

#### 实盘交易
- [实盘交易快速开始](docs_organized/07_实盘交易/LIVE_TRADING_QUICKSTART.md)
- [实盘交易安全指南](docs_organized/07_实盘交易/LIVE_TRADING_SAFETY_GUIDE.md)
- [止盈止损指南](docs_organized/07_实盘交易/STOP_LOSS_TAKE_PROFIT_GUIDE.md)

#### 数据管道
- [数据管道概览](docs_organized/05_数据管道/DATA_PIPELINE.md)
- [数据流程总结](docs_organized/05_数据管道/DATA_FLOW_SUMMARY.md)
- [数据质量验证](docs_organized/05_数据管道/DATA_PIPELINE_VERIFICATION.md)

#### 问题诊断
- [诊断总结](docs_organized/12_其他/DIAGNOSIS_SUMMARY.md)
- [修复验证报告](docs_organized/12_其他/FIX_VERIFICATION_REPORT.md)
- [项目状态概览](docs_organized/12_其他/PROJECT_STATUS_OVERVIEW.md)

## 📁 文档分类 (12 类, 157 个文件)

| 分类 | 文件数 | 说明 |
|------|--------|------|
| [01_快速开始](docs_organized/01_快速开始/) | 6 | 项目入门、快速开始 |
| [02_配置指南](docs_organized/02_配置指南/) | 3 | API、环境配置 |
| [03_架构设计](docs_organized/03_架构设计/) | 4 | 系统架构、设计文档 |
| [04_工作流程](docs_organized/04_工作流程/) | 2 | 工作流程、策略开发 |
| [05_数据管道](docs_organized/05_数据管道/) | 10 | 数据处理、质量控制 |
| [06_日志系统](docs_organized/06_日志系统/) | 8 | 日志使用指南 |
| [07_实盘交易](docs_organized/07_实盘交易/) | 7 | 实盘交易相关 |
| [08_测试验证](docs_organized/08_测试验证/) | 4 | 测试、验证报告 |
| [09_项目报告](docs_organized/09_项目报告/) | 10 | 项目进展报告 |
| [10_问题修复](docs_organized/10_问题修复/) | 7 | Bug 修复、优化 |
| [11_检查清单](docs_organized/11_检查清单/) | 1 | 任务检查清单 |
| [12_其他](docs_organized/12_其他/) | 95 | 归档和详细文档 |

## 🔍 如何查找文档

### 方法 1: 查看索引
```bash
# 查看完整文档索引
cat docs_organized/README.md

# 查看分类摘要
cat docs_organized/SUMMARY.md
```

### 方法 2: 直接浏览
```bash
# 浏览特定分类
ls docs_organized/01_快速开始/
ls docs_organized/07_实盘交易/
ls docs_organized/05_数据管道/
```

### 方法 3: 搜索文档
```bash
# 搜索包含特定关键词的文档
grep -r "关键词" docs_organized/
```

## 📝 项目核心信息

### 系统状态
- ✅ 所有步骤(Step 1-7)已完成并验证
- ✅ 数据归档功能正常(Parquet + Stats)
- ✅ 多时间框架数据对齐已实现
- ✅ 实盘交易系统已就绪

### 关键特性
- 多时间框架数据处理 (5m, 15m, 1h, 4h, 1d)
- 完整的技术指标计算 (MACD, RSI, OBV 等)
- 特征工程和数据归一化
- LLM 决策集成
- 完整的数据归档和审计跟踪

### 数据流程
```
Step 1: K线数据获取
  ↓
Step 2: 技术指标计算
  ↓
Step 3: 特征工程
  ↓
Step 4: 数据质量检查
  ↓
Step 5: LLM 提示生成
  ↓
Step 6: LLM 决策
  ↓
Step 7: 交易信号输出
```

## 📞 获取帮助

1. **查看文档**: 从 `docs_organized/` 查找相关文档
2. **检查日志**: 查看 `logs/` 目录下的日志文件
3. **数据验证**: 查看 `data/` 目录下的归档数据
4. **问题诊断**: 参考 `docs_organized/12_其他/DIAGNOSIS_SUMMARY.md`

## 🎉 最新更新

**2024-12-19**:
- ✅ 安装 pyarrow,修复 Step2/3 数据归档问题
- ✅ 验证所有步骤的 Parquet + Stats 文件生成
- ✅ 整理 157 个文档到 docs_organized 目录
- ✅ 生成完整的文档索引和分类摘要

---

**查看完整整理报告**: [DOCS_ORGANIZATION_REPORT.md](DOCS_ORGANIZATION_REPORT.md)
