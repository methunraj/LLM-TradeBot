#!/usr/bin/env python3
"""
测试多Agent数据归档功能
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from datetime import datetime
from src.utils.data_saver import DataSaver
from src.agents import (
    DataSyncAgent,
    QuantAnalystAgent,
    DecisionCoreAgent,
    RiskAuditAgent,
    PositionInfo,
    RiskLevel
)
from src.api.binance_client import BinanceClient


async def test_data_archiving():
    """测试多Agent数据归档"""
    print("\n" + "="*80)
    print("🧪 测试多Agent数据归档功能")
    print("="*80)
    
    # 初始化
    saver = DataSaver()
    client = BinanceClient()
    
    # Test 1: DataSyncAgent数据归档
    print("\n[1/5] 测试 DataSyncAgent 数据归档...")
    try:
        data_sync = DataSyncAgent(client)
        snapshot = await data_sync.fetch_all_timeframes('BTCUSDT')
        
        files = saver.save_market_snapshot(
            snapshot=snapshot,
            duration=0.44,
            symbol='BTCUSDT'
        )
        
        print(f"  ✅ 保存成功:")
        print(f"     JSON: {files['json']}")
        print(f"     LOG: {files['log']}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: QuantAnalystAgent数据归档
    print("\n[2/5] 测试 QuantAnalystAgent 数据归档...")
    try:
        quant = QuantAnalystAgent()
        signals = await quant.analyze_all_timeframes(snapshot)
        
        files = saver.save_quant_signals(
            signals=signals,
            duration=0.15,
            symbol='BTCUSDT'
        )
        
        print(f"  ✅ 保存成功:")
        print(f"     JSON: {files['json']}")
        print(f"     REPORT: {files['report']}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: DecisionCoreAgent数据归档
    print("\n[3/5] 测试 DecisionCoreAgent 数据归档...")
    try:
        decision = DecisionCoreAgent()
        vote_result = await decision.make_decision(signals)
        
        files = saver.save_vote_result(
            vote_result=vote_result,
            vote_details=vote_result.vote_details,
            weights={
                'trend_5m': 0.15,
                'trend_15m': 0.25,
                'trend_1h': 0.35,
                'oscillator_5m': 0.08,
                'oscillator_15m': 0.12,
                'oscillator_1h': 0.15
            },
            duration=0.01,
            symbol='BTCUSDT'
        )
        
        print(f"  ✅ 保存成功:")
        print(f"     JSON: {files['json']}")
        print(f"     LOG: {files['log']}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: RiskAuditAgent数据归档
    print("\n[4/5] 测试 RiskAuditAgent 数据归档...")
    try:
        audit = RiskAuditAgent()
        
        current_price = snapshot.live_5m.get('close')
        order_before = {
            'action': 'long',
            'entry_price': current_price,
            'stop_loss': current_price * 1.01,  # 错误方向
            'take_profit': current_price * 1.04,
            'quantity': 0.001,
            'leverage': 2.0,
            'confidence': 0.75
        }
        
        audit_result = await audit.audit_decision(
            decision=order_before,
            current_position=None,
            account_balance=10000.0,
            current_price=current_price
        )
        
        # 应用修正
        order_after = order_before.copy()
        if audit_result.corrections:
            order_after.update(audit_result.corrections)
        
        checks = [
            "✅ 逆向开仓检查: 通过",
            "⚠️ 止损方向检查: 需修正",
            "✅ 保证金检查: 通过",
            "✅ 杠杆检查: 通过",
            "✅ 仓位占比检查: 通过",
            "✅ 风险敞口检查: 通过"
        ]
        
        files = saver.save_audit_result(
            audit_result=audit_result,
            order_before=order_before,
            order_after=order_after,
            checks=checks,
            duration=0.02,
            symbol='BTCUSDT'
        )
        
        print(f"  ✅ 保存成功:")
        print(f"     JSON: {files['json']}")
        print(f"     LOG: {files['log']}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: 完整交易循环归档
    print("\n[5/5] 测试完整交易循环归档...")
    try:
        cycle_data = {
            'cycle_id': f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_test123",
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_duration_sec': 0.62,
            'status': 'hold',
            'symbol': 'BTCUSDT',
            'steps': {
                'step1_data_sync': {
                    'duration': 0.44,
                    'status': 'success',
                    'output_file': files['json']
                },
                'step2_quant_analysis': {
                    'duration': 0.15,
                    'status': 'success'
                },
                'step3_decision_core': {
                    'duration': 0.01,
                    'status': 'success'
                },
                'step4_risk_audit': {
                    'duration': 0.02,
                    'status': 'success'
                },
                'step5_execution': {
                    'duration': 0.0,
                    'status': 'skipped',
                    'reason': 'decision=hold'
                }
            },
            'final_result': {
                'action': 'hold',
                'reason': '加权得分21.8未达开仓阈值30'
            }
        }
        
        files = saver.save_trading_cycle(
            cycle_data=cycle_data,
            symbol='BTCUSDT'
        )
        
        print(f"  ✅ 保存成功:")
        print(f"     JSON: {files['json']}")
        print(f"     LOG: {files['log']}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("🎉 数据归档测试完成！")
    print("="*80)
    print("\n查看保存的文件:")
    print(f"  cd data/multi_agent/")
    print(f"  ls -lR")


if __name__ == '__main__':
    asyncio.run(test_data_archiving())
