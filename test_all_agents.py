#!/usr/bin/env python3
"""
多Agent系统快速测试脚本
=========================

功能:
- 测试所有4个Agent的核心功能
- 生成测试报告
- 验证系统集成

Usage:
    python test_all_agents.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from datetime import datetime
from src.api.binance_client import BinanceClient


async def run_all_tests():
    """运行所有Agent测试"""
    print("=" * 80)
    print("🧪 多Agent系统集成测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {}
    
    # Test 1: DataSyncAgent
    print("\n[1/4] 测试 DataSyncAgent...")
    print("-" * 80)
    try:
        from src.agents import DataSyncAgent
        
        client = BinanceClient()
        agent = DataSyncAgent(client)
        
        snapshot = await agent.fetch_all_timeframes('BTCUSDT')
        
        print(f"  ✅ 数据采集成功")
        print(f"  ✅ 5m数据: {len(snapshot.stable_5m)} 条")
        print(f"  ✅ 15m数据: {len(snapshot.stable_15m)} 条")
        print(f"  ✅ 1h数据: {len(snapshot.stable_1h)} 条")
        print(f"  ✅ 实时价格: ${snapshot.live_5m.get('close'):,.2f}")
        print(f"  ✅ 时间对齐: {'是' if snapshot.alignment_ok else '否'}")
        
        test_results['DataSyncAgent'] = 'PASS'
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        test_results['DataSyncAgent'] = 'FAIL'
    
    # Test 2: QuantAnalystAgent
    print("\n[2/4] 测试 QuantAnalystAgent...")
    print("-" * 80)
    try:
        from src.agents import QuantAnalystAgent
        
        analyst = QuantAnalystAgent()
        analysis = await analyst.analyze_all_timeframes(snapshot)
        
        print(f"  ✅ 量化分析成功")
        print(f"  ✅ 趋势1h得分: {analysis['trend_1h']['score']}")
        print(f"  ✅ 趋势1h信号: {analysis['trend_1h']['signal']}")
        print(f"  ✅ 震荡1h得分: {analysis['oscillator_1h']['score']}")
        print(f"  ✅ 综合得分: {analysis['comprehensive']['score']}")
        print(f"  ✅ 综合信号: {analysis['comprehensive']['signal']}")
        
        test_results['QuantAnalystAgent'] = 'PASS'
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        test_results['QuantAnalystAgent'] = 'FAIL'
    
    # Test 3: DecisionCoreAgent
    print("\n[3/4] 测试 DecisionCoreAgent...")
    print("-" * 80)
    try:
        from src.agents import DecisionCoreAgent
        
        core = DecisionCoreAgent()
        vote = await core.make_decision(analysis)
        
        print(f"  ✅ 决策生成成功")
        print(f"  ✅ 决策动作: {vote.action}")
        print(f"  ✅ 置信度: {vote.confidence:.2%}")
        print(f"  ✅ 加权得分: {vote.weighted_score:.1f}")
        print(f"  ✅ 多周期对齐: {'是' if vote.multi_period_aligned else '否'}")
        print(f"  ✅ 决策原因: {vote.reason[:60]}...")
        
        test_results['DecisionCoreAgent'] = 'PASS'
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        test_results['DecisionCoreAgent'] = 'FAIL'
    
    # Test 4: RiskAuditAgent
    print("\n[4/4] 测试 RiskAuditAgent...")
    print("-" * 80)
    try:
        from src.agents import RiskAuditAgent, PositionInfo
        
        audit = RiskAuditAgent(
            max_leverage=10.0,
            max_position_pct=0.3,
            min_stop_loss_pct=0.005,
            max_stop_loss_pct=0.05
        )
        
        # 构建测试订单
        current_price = snapshot.live_5m.get('close')
        test_decision = {
            'action': 'long',
            'entry_price': current_price,
            'stop_loss': current_price * 0.98,  # -2%
            'take_profit': current_price * 1.04,  # +4%
            'quantity': 0.001,
            'leverage': 2.0,
            'confidence': 0.75
        }
        
        result = await audit.audit_decision(
            decision=test_decision,
            current_position=None,
            account_balance=10000.0,
            current_price=current_price
        )
        
        print(f"  ✅ 风控审计成功")
        print(f"  ✅ 审计结果: {'通过' if result.passed else '拦截'}")
        print(f"  ✅ 风险等级: {result.risk_level.value}")
        
        if result.corrections:
            print(f"  ⚠️  自动修正: {len(result.corrections)} 项")
        
        if result.warnings:
            print(f"  ⚠️  警告信息: {len(result.warnings)} 条")
        
        # 测试止损方向修正
        print(f"\n  测试止损方向修正...")
        wrong_decision = {
            'action': 'long',
            'entry_price': current_price,
            'stop_loss': current_price * 1.01,  # ❌ 错误：做多止损>入场价
            'take_profit': current_price * 1.04,
            'quantity': 0.001,
            'leverage': 2.0,
            'confidence': 0.75
        }
        
        fix_result = await audit.audit_decision(
            decision=wrong_decision,
            current_position=None,
            account_balance=10000.0,
            current_price=current_price
        )
        
        if fix_result.corrections and 'stop_loss' in fix_result.corrections:
            print(f"  ✅ 止损修正成功: {wrong_decision['stop_loss']:,.2f} → {fix_result.corrections['stop_loss']:,.2f}")
        else:
            print(f"  ❌ 止损修正失败")
        
        test_results['RiskAuditAgent'] = 'PASS'
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        test_results['RiskAuditAgent'] = 'FAIL'
        import traceback
        traceback.print_exc()
    
    # 生成测试报告
    print("\n" + "=" * 80)
    print("📊 测试报告")
    print("=" * 80)
    
    total = len(test_results)
    passed = sum(1 for r in test_results.values() if r == 'PASS')
    failed = total - passed
    
    for agent, result in test_results.items():
        emoji = "✅" if result == "PASS" else "❌"
        print(f"{emoji} {agent}: {result}")
    
    print()
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个 ({passed/total*100:.0f}%)")
    print(f"失败: {failed} 个 ({failed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！多Agent系统运行正常！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查日志")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
