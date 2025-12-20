# 数据质量门控实现总结

## ❌ 问题诊断: 趋势判断基于不可靠数据

您提出的核心问题:

```python
if sma_20 > sma_50 and price > sma_20:
    uptrend
```

但是:
- ~~SMA 来自被 MAD 裁剪的数据~~  ✅ 已修复
- ~~EMA warmup 不充分~~  ✅ 已修复  
- ~~多周期未对齐~~  ⏳ 部分修复

**当前状态:**
- MAD裁剪已移除 (KlineValidator仅检测真正错误)
- Warmup期提升到105根 (MACD完全收敛)
- 多周期价格一致性检查已添加
- **缺失: 数据质量门控机制** 👈 今天要完成的

---

## ✅ 已完成的修复

### 1. processor.py: 指标完整性检查

```python
def check_indicator_completeness(self, df: pd.DataFrame, min_coverage: float = 0.95) -> Dict:
    """
    检查技术指标完整性
    
    检查项:
    1. 关键指标是否包含 NaN/Inf
    2. 数据覆盖率是否达标
    3. warm-up期是否完成
    
    Returns:
        {
            'is_complete': bool,
            'issues': List[str],
            'coverage': Dict[str, float],
            'overall_coverage': float
        }
    """
```

**功能:**
- 检查14个关键指标的NaN/Inf情况
- 计算每个指标的覆盖率
- 验证warmup期完成状态
- 生成总体质量评分

### 2. builder.py: 数据质量报告

```python
'data_quality': {
    'price_consistency': price_check,        # 多周期价格一致性
    'time_alignment': alignment_check,       # 时间对齐验证
    'indicator_completeness': indicator_completeness,  # 指标完整性
    'overall_score': float  # 综合质量分数 (0-100)
}
```

**质量评分算法:**
```python
def _calculate_quality_score(price_check, alignment_check, indicator_completeness) -> float:
    score = 100.0
    
    # 价格一致性 (权重: 30%)
    if not price_check['consistent']:
        score -= 30
    
    # 时间对齐 (权重: 20%)
    if not alignment_check['aligned']:
        score -= 20
    
    # 指标完整性 (权重: 50%)
    avg_completeness = mean([comp['overall_coverage'] for comp in indicator_completeness.values()])
    score -= (100 - avg_completeness * 100) * 0.5
    
    return max(score, 0.0)
```

### 3. run_live_trading.py: 数据采集时检查指标完整性

```python
# 🆕 检查指标完整性（每个周期）
for tf, df in [('5m', df_5m), ('15m', df_15m), ('1h', df_1h)]:
    completeness = self.processor.check_indicator_completeness(df, min_coverage=0.95)
    multi_timeframe_states[tf]['indicator_completeness'] = completeness
    
    if not completeness['is_complete']:
        log.warning(f"[{symbol}] {tf}周期指标不完整:")
        for issue in completeness['issues'][:5]:
            log.warning(f"  - {issue}")
        log.warning(f"  总体覆盖率: {completeness['overall_coverage']:.1%}")
```

---

## ⏳ 待完成: 数据质量门控逻辑

### 问题

run_live_trading.py文件在1040-1180行损坏,需要修复后才能添加质量门控逻辑。

### 计划实现

在`generate_signal()`方法开头添加质量检查:

```python
def generate_signal(self, market_state: Dict) -> str:
    """
    生成交易信号 - 多层决策架构
    
    ⚠️ 新增: 数据质量门控
    - 如果数据质量分数 < 阈值 → 强制HOLD
    - 防止基于低质量数据做决策
    """
    
    # === 🆕 Layer 0: 数据质量门控 ===
    data_quality = market_state.get('data_quality', {})
    quality_score = data_quality.get('overall_score', 0)
    
    # 质量阈值: 60分
    MIN_QUALITY_SCORE = 60.0
    
    if quality_score < MIN_QUALITY_SCORE:
        print(f"\n⛔ 数据质量不足: {quality_score:.1f}/100 < {MIN_QUALITY_SCORE}")
        
        # 显示质量问题详情
        if 'price_consistency' in data_quality:
            price_check = data_quality['price_consistency']
            if not price_check['consistent']:
                print("  ❌ 价格一致性检查失败:")
                for warning in price_check['warnings']:
                    print(f"     - {warning}")
        
        if 'time_alignment' in data_quality:
            alignment_check = data_quality['time_alignment']
            if not alignment_check['aligned']:
                print("  ❌ 时间对齐检查失败:")
                for warning in alignment_check['warnings']:
                    print(f"     - {warning}")
        
        if 'indicator_completeness' in data_quality:
            indicator_comp = data_quality['indicator_completeness']
            for tf, comp in indicator_comp.items():
                if not comp.get('is_complete'):
                    print(f"  ❌ {tf}周期指标不完整:")
                    for issue in comp['issues'][:3]:
                        print(f"     - {issue}")
        
        print("  → 强制HOLD信号，等待数据质量改善")
        
        # 强制返回HOLD
        return 'HOLD'
    
    # 数据质量通过，继续正常决策流程
    print(f"\n✅ 数据质量检查通过: {quality_score:.1f}/100")
    
    # Layer 1: 基础规则信号
    base_signal = self._basic_rule_signal(market_state)
    
    # Layer 2: 增强规则信号
    enhanced_signal = self._enhanced_rule_signal(market_state)
    
    # Layer 3: 风险过滤
    risk_veto = self._risk_filter(market_state)
    
    # 决策融合
    final_signal = self._merge_signals(base_signal, enhanced_signal, risk_veto)
    
    return final_signal
```

---

## 📋 测试计划

创建测试脚本验证质量门控:

```python
# test_data_quality_gating.py

def test_low_quality_triggers_hold():
    """测试低质量数据触发HOLD"""
    market_state = {
        'data_quality': {
            'overall_score': 40.0,  # 低于60
            'price_consistency': {'consistent': False, 'warnings': ['价格不一致']},
            'indicator_completeness': {
                '5m': {'is_complete': False, 'issues': ['sma_20包含NaN']}
            }
        },
        'timeframes': {...}  # 正常的市场数据
    }
    
    signal = bot.generate_signal(market_state)
    assert signal == 'HOLD', "低质量数据应返回HOLD"
    
def test_high_quality_allows_normal_decision():
    """测试高质量数据允许正常决策"""
    market_state = {
        'data_quality': {
            'overall_score': 95.0,  # 高分
            'price_consistency': {'consistent': True},
            'indicator_completeness': {
                '5m': {'is_complete': True},
                '15m': {'is_complete': True},
                '1h': {'is_complete': True}
            }
        },
        'timeframes': {
            '5m': {'trend': 'uptrend', 'rsi': 65},
            '15m': {'trend': 'uptrend', 'rsi': 68},
            '1h': {'trend': 'uptrend', 'rsi': 62}
        }
    }
    
    signal = bot.generate_signal(market_state)
    # 应该正常执行决策逻辑，可能是BUY/SELL/HOLD（取决于规则）
    assert signal in ['BUY', 'SELL', 'HOLD']
```

---

## 🔄 数据流向（修正后）

```
Step1: 获取K线数据
   ↓
Step2: 计算技术指标
   ↓
   ├──→ check_indicator_completeness()  ✅ 新增
   │    - 检查NaN/Inf
   │    - 验证warmup
   │    - 计算覆盖率
   ↓
Step3: 特征工程
   ↓
Step4: 构建市场上下文
   ↓
   ├──→ _validate_multiframe_prices()  ✅ 已有
   ├──→ _validate_multiframe_alignment()  ✅ 已有
   ├──→ _calculate_quality_score()  ✅ 新增
   │    - 综合评分 (0-100)
   ↓
Step5: 生成信号
   ↓
   ├──→ 🆕 Layer 0: 数据质量门控
   │    if quality_score < 60:
   │        return 'HOLD'  ← 强制门控
   ↓
   ├──→ Layer 1: 基础规则
   ├──→ Layer 2: 增强规则
   ├──→ Layer 3: 风险过滤
   ↓
Step6: 执行交易
```

---

## 📊 质量门控阈值设计

| 质量分数 | 状态 | 行为 |
|---------|------|------|
| 90-100 | 优秀 | 正常交易 |
| 70-89 | 良好 | 正常交易 |
| 60-69 | 及格 | 正常交易（警告）|
| 50-59 | 不及格 | **强制HOLD** |
| 0-49 | 严重问题 | **强制HOLD** |

**阈值选择: 60分**

原因:
1. 保守策略: 宁可错过机会，不冒质量风险
2. 数据完整性权重50%: 确保指标可用
3. 价格一致性权重30%: 确保多周期可靠
4. 时间对齐权重20%: 确保数据同步

---

## 📝 待修复文件

**run_live_trading.py (1040-1180行损坏)**

需要手动清理损坏的代码，然后添加质量门控逻辑。

建议步骤:
1. 删除1040-1180行的损坏代码
2. 恢复正确的函数定义
3. 在generate_signal开头添加Layer 0质量门控
4. 运行测试验证

---

## 🎯 完成标准

✅ processor.py: check_indicator_completeness() 实现
✅ builder.py: 数据质量报告集成
✅ run_live_trading.py: 数据采集时检查完整性
⏳ run_live_trading.py: generate_signal中添加质量门控
⏳ test_data_quality_gating.py: 自动化测试
⏳ DATA_FLOW_STRUCTURED.md: 更新文档

---

**最后更新:** 2025-12-18
**状态:** 70% 完成，等待文件修复后继续
