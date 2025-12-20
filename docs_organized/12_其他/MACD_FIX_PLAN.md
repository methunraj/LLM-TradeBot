# MACD"魔改"问题修复方案

## 问题诊断

### 当前实现（processor.py line 156-168）
```python
# 归一化：MACD / Price * 100 转为百分比
df['macd'] = (macd_raw / df['close']) * 100
df['macd_signal'] = (macd_signal_raw / df['close']) * 100
df['macd_diff'] = (macd_diff_raw / df['close']) * 100
```

### 核心问题
1. **量纲破坏**：经典MACD是价差（USDT），现在变成了百分比（%）
2. **失去物理意义**：MACD本应反映绝对价格动量，现在只反映相对比例
3. **信号失真**：金叉/死叉的阈值判断逻辑需要重新校准
4. **回测失效**：历史策略的MACD阈值（如±0.1）现在毫无意义

### 数值对比示例
假设BTC价格在87000 USDT：
- **经典MACD**：EMA12 - EMA26 = 87150 - 87000 = **150 USDT**
- **魔改MACD**：150 / 87000 * 100 = **0.172%**

两者完全不可比！

---

## 修复方案

### 阶段1：保留原始MACD（Step2）
**目标**：在Step2技术指标计算中，保存**经典价差版本**的MACD

**代码修改**（processor.py）：
```python
# Step2: 保存原始MACD价差（USDT）
macd_indicator = MACD(close=df['close'])
df['macd'] = macd_indicator.macd()              # 原始价差（USDT）
df['macd_signal'] = macd_indicator.macd_signal()  # 信号线（USDT）
df['macd_diff'] = macd_indicator.macd_diff()     # 柱状图（USDT）
```

**验证点**：
- MACD数值应在±100~±1000 USDT范围（视市场波动）
- 单位：USDT（与价格同量纲）
- 金叉/死叉以0为界

---

### 阶段2：特征工程归一化（Step3）
**目标**：在Step3特征工程中，**可选地**添加归一化版本供模型训练

**新增特征**（feature_engineering.py或processor.py的特征部分）：
```python
# Step3: 特征工程 - 创建归一化版本
df['macd_pct'] = (df['macd'] / df['close']) * 100           # 百分比版本
df['macd_signal_pct'] = (df['macd_signal'] / df['close']) * 100
df['macd_diff_pct'] = (df['macd_diff'] / df['close']) * 100

# 或使用标准化（更推荐）
df['macd_std'] = (df['macd'] - df['macd'].rolling(100).mean()) / df['macd'].rolling(100).std()
```

**命名规范**：
- `macd`, `macd_signal`, `macd_diff`：原始价差（USDT）
- `macd_pct`, `macd_signal_pct`, `macd_diff_pct`：百分比版本
- `macd_std`, `macd_signal_std`, `macd_diff_std`：标准化版本

---

### 阶段3：信号系统调整（Step5/Step6）
**目标**：更新信号生成逻辑，使用经典MACD阈值

**修改示例**（run_live_trading.py或signal_generator.py）：
```python
# 旧版（百分比阈值，已失效）
if macd > 0.1 and macd_diff > 0:  # ❌ 错误！
    signal = 'BUY'

# 新版（价差阈值）
if macd > 50 and macd_diff > 0:  # ✅ 正确（50 USDT阈值）
    signal = 'BUY'
```

**阈值校准方法**：
1. 统计历史MACD分布（均值、标准差、分位数）
2. 根据回测结果调整阈值
3. 建议使用动态阈值（如MACD的20日移动平均）

---

## 修复步骤

### Step1: 备份当前代码
```bash
cp src/data/processor.py src/data/processor.py.bak
cp run_live_trading.py run_live_trading.py.bak
```

### Step2: 修改processor.py
1. 删除line 164-168的归一化代码
2. 保留原始MACD计算（line 159-162）
3. （可选）在特征工程部分添加归一化版本

### Step3: 更新信号系统
1. 检查所有MACD相关的if条件（grep "macd"）
2. 将百分比阈值（0.01~1.0）改为价差阈值（10~500 USDT）
3. 或使用动态阈值（如MACD > MACD.mean()）

### Step4: 重新处理历史数据
```bash
# 删除旧的Step2数据（包含魔改MACD）
rm -rf data/step2/

# 重新运行数据处理
python run_live_trading.py --reprocess-all
```

### Step5: 验证修复结果
运行验证脚本（见下方）

---

## 验证清单

### ✅ 数据验证
- [ ] MACD数值在合理范围（±100~±1000 USDT）
- [ ] MACD单位为价差（USDT），非百分比
- [ ] MACD金叉/死叉以0为界
- [ ] MACD与价格同向变动

### ✅ 代码验证
- [ ] processor.py不再对MACD做归一化
- [ ] Step2输出文件包含原始MACD
- [ ] 信号系统使用合理的价差阈值
- [ ] 特征工程（如有）明确标注归一化字段

### ✅ 回测验证
- [ ] 重新回测历史策略，确认信号准确性
- [ ] 对比修复前后的收益率/胜率
- [ ] 检查MACD交叉信号的触发时机

---

## 影响评估

### 需要重新处理的数据
- ❌ 所有Step2技术指标文件（MACD被魔改）
- ❌ 所有Step3特征文件（依赖错误的MACD）
- ❌ 所有Step5/Step6信号文件（使用错误的MACD）
- ✅ Step1原始K线（无影响）

### 需要调整的策略参数
- MACD相关的买卖阈值
- MACD交叉信号的确认条件
- 止损/止盈逻辑（如依赖MACD动量）

### 预期收益
1. **信号准确性提升**：MACD恢复经典定义，与技术分析理论一致
2. **策略可解释性增强**：交易员可直接理解MACD价差的含义
3. **跨市场可移植性**：MACD定义标准化，适用于其他资产
4. **模型训练改进**：特征工程更灵活（可同时使用原始值和归一化值）

---

## 参考资料

### MACD经典定义
- **MACD线**：12日EMA - 26日EMA（价差，单位同价格）
- **信号线**：MACD的9日EMA
- **柱状图**：MACD - 信号线
- **金叉**：MACD上穿信号线（0轴上方更强）
- **死叉**：MACD下穿信号线（0轴下方更强）

### 归一化的正确时机
- ❌ **错误**：在Step2技术指标计算时归一化
- ✅ **正确**：在Step3特征工程时，为模型训练创建多版本特征
- ✅ **正确**：在模型输入前，对所有特征做统一的标准化/归一化

---

## 修复时间表

1. **立即**：创建验证脚本，确认问题严重性
2. **1小时内**：修改processor.py，恢复经典MACD
3. **2小时内**：更新信号系统，重新校准阈值
4. **4小时内**：重新处理历史数据，验证修复效果
5. **1天内**：回测策略，对比修复前后差异

---

*Last Updated: 2025-12-17*  
*Author: Architecture Review Team*
