"""
🤖 LLM-TradeBot - 多Agent架构主循环
===========================================

集成:
1. 🕵️ DataSyncAgent - 异步并发数据采集
2. 👨‍🔬 QuantAnalystAgent - 量化信号分析
3. ⚖️ DecisionCoreAgent - 加权投票决策
4. 👮 RiskAuditAgent - 风控审计拦截

优化:
- 异步并发执行（减少60%等待时间）
- 双视图数据结构（stable + live）
- 分层信号分析（趋势 + 震荡）
- 多周期对齐决策
- 止损方向自动修正
- 一票否决风控

Author: AI Trader Team
Date: 2025-12-19
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from typing import Dict, Optional
from datetime import datetime
import json
import time

from src.api.binance_client import BinanceClient
from src.execution.engine import ExecutionEngine
from src.risk.manager import RiskManager
from src.config import Config
from src.utils.logger import log
from src.utils.trade_logger import trade_logger
from src.utils.data_saver import DataSaver
from src.data.processor import MarketDataProcessor
from dataclasses import asdict

# 导入多Agent
from src.agents import (
    DataSyncAgent,
    QuantAnalystAgent,
    DecisionCoreAgent,
    RiskAuditAgent,
    PositionInfo,
    SignalWeight
)

class MultiAgentTradingBot:
    """
    多Agent交易机器人（重构版）
    
    工作流程:
    1. DataSyncAgent: 异步采集5m/15m/1h数据
    2. QuantAnalystAgent: 生成量化信号（趋势+震荡）
    3. DecisionCoreAgent: 加权投票决策
    4. RiskAuditAgent: 风控审计拦截
    5. ExecutionEngine: 执行交易
    """
    
    def __init__(
        self,
        max_position_size: float = 100.0,
        leverage: int = 1,
        stop_loss_pct: float = 1.0,
        take_profit_pct: float = 2.0,
        test_mode: bool = False
    ):
        """
        初始化多Agent交易机器人
        
        Args:
            max_position_size: 最大单笔金额（USDT）
            leverage: 杠杆倍数
            stop_loss_pct: 止损百分比
            take_profit_pct: 止盈百分比
            test_mode: 测试模式（不执行真实交易）
        """
        print("\n" + "="*80)
        print("🤖 AI Trader - 多Agent架构版本")
        print("="*80)
        
        self.config = Config()
        self.symbol = self.config.get('trading.symbol', 'BTCUSDT')
        self.test_mode = test_mode
        
        # 交易参数
        self.max_position_size = max_position_size
        self.leverage = leverage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        
        # 初始化客户端
        self.client = BinanceClient()
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine(self.client, self.risk_manager)
        self.saver = DataSaver() # ✅ 初始化 Multi-Agent 数据保存器
        
        # 初始化4大Agent
        print("\n🚀 初始化Agent...")
        self.data_sync_agent = DataSyncAgent(self.client)
        self.quant_analyst = QuantAnalystAgent()
        self.decision_core = DecisionCoreAgent()
        self.risk_audit = RiskAuditAgent(
            max_leverage=10.0,
            max_position_pct=0.3,
            min_stop_loss_pct=0.005,
            max_stop_loss_pct=0.05
        )
        self.processor = MarketDataProcessor()  # ✅ 初始化数据处理器
        
        print("  ✅ DataSyncAgent 已就绪")
        print("  ✅ QuantAnalystAgent 已就绪")
        print("  ✅ DecisionCoreAgent 已就绪")
        print("  ✅ RiskAuditAgent 已就绪")
        
        print(f"\n⚙️  交易配置:")
        print(f"  - 交易对: {self.symbol}")
        print(f"  - 最大单笔: ${self.max_position_size:.2f} USDT")
        print(f"  - 杠杆倍数: {self.leverage}x")
        print(f"  - 止损: {self.stop_loss_pct}%")
        print(f"  - 止盈: {self.take_profit_pct}%")
        print(f"  - 测试模式: {'✅ 是' if self.test_mode else '❌ 否'}")
    
    async def run_trading_cycle(self) -> Dict:
        """
        执行完整的交易循环（异步版本）
        
        Returns:
            {
                'status': 'success/failed/hold/blocked',
                'action': 'long/short/hold',
                'details': {...}
            }
        """
        print(f"\n{'='*80}")
        print(f"🔄 启动交易审计循环 | {datetime.now().strftime('%H:%M:%S')} | {self.symbol}")
        print(f"{'='*80}")
        
        try:
            # ✅ Generate snapshot_id for this cycle
            snapshot_id = f"snap_{int(time.time())}"

            # Step 1: 采样 - 数据先知 (The Oracle)
            print("\n[Step 1/4] 🕵️ 数据先知 (The Oracle) - 异步数据采集...")
            market_snapshot = await self.data_sync_agent.fetch_all_timeframes(self.symbol)
            
            # ✅ Save Market Data & Process Indicators
            processed_dfs = {}
            for tf in ['5m', '15m', '1h']:
                raw_klines = getattr(market_snapshot, f'raw_{tf}')
                # 保存原始数据
                self.saver.save_market_data(raw_klines, self.symbol, tf)
                
                # 处理并保存指标 (Process indicators)
                df_with_indicators = self.processor.process_klines(raw_klines, self.symbol, tf)
                self.saver.save_indicators(df_with_indicators, self.symbol, tf, snapshot_id)
                
                # 提取并保存特征 (Extract features)
                features_df = self.processor.extract_feature_snapshot(df_with_indicators)
                self.saver.save_features(features_df, self.symbol, tf, snapshot_id)
                
                # 存入字典供后续步骤复用
                processed_dfs[tf] = df_with_indicators
                
            # ✅ 重要优化：更新快照中的 DataFrame，使其携带技术指标
            # 这样 QuantAnalystAgent 内部就不需要再次计算指标了
            market_snapshot.stable_5m = processed_dfs['5m']
            market_snapshot.stable_15m = processed_dfs['15m']
            market_snapshot.stable_1h = processed_dfs['1h']
            
            current_price = market_snapshot.live_5m.get('close')
            print(f"  ✅ 采样完毕: ${current_price:,.2f} ({market_snapshot.timestamp.strftime('%H:%M:%S')})")
            
            # Step 2: 假设 - 量化策略师 (The Strategist)
            print("[Step 2/4] 👨‍🔬 量化策略师 (The Strategist) - 评估数据中...")
            quant_analysis = await self.quant_analyst.analyze_all_timeframes(market_snapshot)
            
            # ✅ Save Quant Analysis (Analytics)
            self.saver.save_context(quant_analysis, self.symbol, 'analytics', snapshot_id)
            
            # Step 3: 对抗 - 对抗评论员 (The Critic)
            print("[Step 3/4] ⚖️ 对抗评论员 (The Critic) - 极速审理信号...")
            # ✅ 复用 Step 1 已处理的数据，避免第三次计算
            market_data = {
                'df_5m': processed_dfs['5m'],
                'df_15m': processed_dfs['15m'],
                'df_1h': processed_dfs['1h'],
                'current_price': current_price
            }
            
            vote_result = await self.decision_core.make_decision(
                quant_analysis,
                market_data=market_data
            )
            
            # ✅ Save Decision
            self.saver.save_decision(asdict(vote_result), self.symbol, snapshot_id)
            
            # ✅ Generate and Save LLM Context (LLM Logs)
            # 记录输入给决策引擎的完整上下文以及最终投票结果
            llm_context = self.decision_core.to_llm_context(
                vote_result=vote_result, 
                quant_analysis=quant_analysis
            )
            self.saver.save_llm_log(
                content=f"PROMPT: N/A (Agent Voting Consensus)\n\n{llm_context}",
                symbol=self.symbol,
                snapshot_id=snapshot_id
            )
            
            # 如果是观望，直接返回
            if vote_result.action == 'hold':
                print("\n✅ 决策: 观望")
                return {
                    'status': 'hold',
                    'action': 'hold',
                    'details': {
                        'reason': vote_result.reason,
                        'confidence': vote_result.confidence
                    }
                }
            
            # Step 4: 审计 - 风控守护者 (The Guardian)
            print(f"[Step 4/4] 👮 风控守护者 (The Guardian) - 进行终审...")
            order_params = self._build_order_params(
                action=vote_result.action,
                current_price=current_price,
                confidence=vote_result.confidence
            )
            
            print(f"  ✅ 信号方向: {vote_result.action}")
            print(f"  ✅ 综合信心: {vote_result.confidence:.1f}%")
            if vote_result.regime:
                print(f"  📊 市场状态: {vote_result.regime['regime']}")
            if vote_result.position:
                print(f"  📍 价格位置: {vote_result.position['position_pct']:.1f}% ({vote_result.position['location']})")
            
            # 将对抗式上下文注入订单参数，以便风控审计使用
            order_params['regime'] = vote_result.regime
            order_params['position'] = vote_result.position
            order_params['confidence'] = vote_result.confidence
            
            # Step 5 (Embedded in Step 4 for clean output)
            
            # 获取账户信息
            account_balance = self._get_account_balance()
            current_position = self._get_current_position()
            
            # 执行审计
            audit_result = await self.risk_audit.audit_decision(
                decision=order_params,
                current_position=current_position,
                account_balance=account_balance,
                current_price=current_price
            )
            
            # ✅ Save Risk Audit Report
            from dataclasses import asdict as dc_asdict
            self.saver.save_risk_audit(
                audit_result={
                    'passed': audit_result.passed,
                    'risk_level': audit_result.risk_level.value,
                    'blocked_reason': audit_result.blocked_reason,
                    'corrections': audit_result.corrections,
                    'warnings': audit_result.warnings,
                    'order_params': order_params
                },
                symbol=self.symbol,
                snapshot_id=snapshot_id
            )
            
            print(f"  ✅ 审计结果: {'✅ 通过' if audit_result.passed else '❌ 拦截'}")
            print(f"  ✅ 风险等级: {audit_result.risk_level.value}")
            
            # 如果有修正
            if audit_result.corrections:
                print(f"  ⚠️  自动修正:")
                for key, value in audit_result.corrections.items():
                    print(f"     {key}: {order_params[key]} -> {value}")
                    order_params[key] = value  # 应用修正
            
            # 如果有警告
            if audit_result.warnings:
                print(f"  ⚠️  警告信息:")
                for warning in audit_result.warnings:
                    print(f"     {warning}")
            
            # 如果被拦截
            if not audit_result.passed:
                print(f"\n❌ 决策被风控拦截: {audit_result.blocked_reason}")
                return {
                    'status': 'blocked',
                    'action': vote_result.action,
                    'details': {
                        'reason': audit_result.blocked_reason,
                        'risk_level': audit_result.risk_level.value
                    }
                }
            # Step 5: 执行引擎
            if self.test_mode:
                print("\n[Step 5/5] 🧪 TestMode - 模拟执行...")
                print(f"  模拟订单: {order_params['action']} {order_params['quantity']} @ {current_price}")
                
                 # ✅ Save Execution (Simulated)
                self.saver.save_execution({
                    'symbol': self.symbol,
                    'action': 'SIMULATED_EXECUTION',
                    'params': order_params,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }, self.symbol)
                
                # ✅ Save Trade in persistent history
                self.saver.save_trade({
                    'action': order_params['action'].upper(),
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': order_params['quantity'],
                    'cost': current_price * order_params['quantity'],
                    'exit_price': 0,
                    'pnl': 0,
                    'confidence': order_params['confidence'],
                    'status': 'SIMULATED'
                })
                
                return {
                    'status': 'success',
                    'action': vote_result.action,
                    'details': order_params
                }
            
            print("\n[Step 5/5] 🚀 ExecutionEngine - 正在执行...")
            executed = self._execute_order(order_params)
            
            # ✅ Save Execution
            self.saver.save_execution({
                'symbol': self.symbol,
                'action': 'REAL_EXECUTION',
                'params': order_params,
                'status': 'success' if executed else 'failed',
                'timestamp': datetime.now().isoformat()
            }, self.symbol)
            
            if executed:
                print("  ✅ 订单执行成功!")
                
                # 记录交易日志
                trade_logger.log_open_position(
                    symbol=self.symbol,
                    side=order_params['action'].upper(),
                    decision=order_params,
                    execution_result={
                        'success': True,
                        'entry_price': order_params['entry_price'],
                        'quantity': order_params['quantity'],
                        'stop_loss': order_params['stop_loss'],
                        'take_profit': order_params['take_profit'],
                        'order_id': 'real_order' # Placeholder if actual ID not captured
                    },
                    market_state=market_snapshot.live_5m,
                    account_info={'available_balance': account_balance}
                )
                
                # 计算盈亏 (如果是平仓)
                pnl = 0.0
                exit_price = 0.0
                entry_price = order_params['entry_price']
                if order_params['action'] == 'close_position' and current_position:
                    exit_price = current_price
                    entry_price = current_position.entry_price
                    # PnL = (Exit - Entry) * Qty (Multiplied by 1 if long, -1 if short)
                    direction = 1 if current_position.side == 'long' else -1
                    pnl = (exit_price - entry_price) * current_position.quantity * direction
                
                # ✅ Save Trade in persistent history
                self.saver.save_trade({
                    'action': order_params['action'].upper(),
                    'symbol': self.symbol,
                    'price': entry_price,
                    'quantity': order_params['quantity'],
                    'cost': entry_price * order_params['quantity'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'confidence': order_params['confidence'],
                    'status': 'EXECUTED'
                })
                
                return {
                    'status': 'success',
                    'action': vote_result.action,
                    'details': order_params
                }
            else:
                print("  ❌ 订单执行失败")
                return {
                    'status': 'failed',
                    'action': vote_result.action,
                    'details': {'error': 'execution_failed'}
                }
        
        except Exception as e:
            log.error(f"计交易循环异常: {e}", exc_info=True)
            return {
                'status': 'error',
                'details': {'error': str(e)}
            }
    
    def _build_order_params(
        self, 
        action: str, 
        current_price: float,
        confidence: float
    ) -> Dict:
        """
        构建订单参数
        
        Args:
            action: 'long' or 'short'
            current_price: 当前价格
            confidence: 决策置信度
        
        Returns:
            订单参数字典
        """
        # 计算仓位大小（根据置信度调整）
        position_multiplier = min(confidence * 1.2, 1.0)  # 最高100%仓位
        adjusted_position = self.max_position_size * position_multiplier
        
        # 计算数量
        quantity = adjusted_position / current_price
        
        # 计算止损止盈
        if action == 'long':
            stop_loss = current_price * (1 - self.stop_loss_pct / 100)
            take_profit = current_price * (1 + self.take_profit_pct / 100)
        else:  # short
            stop_loss = current_price * (1 + self.stop_loss_pct / 100)
            take_profit = current_price * (1 - self.take_profit_pct / 100)
        
        return {
            'action': action,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'quantity': quantity,
            'leverage': self.leverage,
            'confidence': confidence
        }
    
    def _get_account_balance(self) -> float:
        """获取账户可用余额"""
        try:
            return self.client.get_account_balance()
        except Exception as e:
            log.error(f"获取余额失败: {e}")
            return 0.0
    
    def _get_current_position(self) -> Optional[PositionInfo]:
        """获取当前持仓"""
        try:
            pos = self.client.get_futures_position(self.symbol)
            if pos and abs(pos['position_amt']) > 0:
                return PositionInfo(
                    symbol=self.symbol,
                    side='long' if pos['position_amt'] > 0 else 'short',
                    entry_price=pos['entry_price'],
                    quantity=abs(pos['position_amt']),
                    unrealized_pnl=pos['unrealized_profit']
                )
            return None
        except Exception as e:
            log.error(f"获取持仓失败: {e}")
            return None
    
    def _execute_order(self, order_params: Dict) -> bool:
        """
        执行订单
        
        Args:
            order_params: 订单参数
        
        Returns:
            是否成功
        """
        try:
            # 设置杠杆
            self.client.set_leverage(
                symbol=self.symbol,
                leverage=order_params['leverage']
            )
            
            # 市价开仓
            side = 'BUY' if order_params['action'] == 'long' else 'SELL'
            order = self.client.place_futures_market_order(
                symbol=self.symbol,
                side=side,
                quantity=order_params['quantity']
            )
            
            if not order:
                return False
            
            # 设置止损止盈
            self.execution_engine.set_stop_loss_take_profit(
                symbol=self.symbol,
                position_side='LONG' if order_params['action'] == 'long' else 'SHORT',
                stop_loss=order_params['stop_loss'],
                take_profit=order_params['take_profit']
            )
            
            return True
            
        except Exception as e:
            log.error(f"订单执行失败: {e}", exc_info=True)
            return False
    
    def run_once(self) -> Dict:
        """运行一次交易循环（同步包装）"""
        result = asyncio.run(self.run_trading_cycle())
        self._display_recent_trades()
        return result

    def _display_recent_trades(self):
        """显示最近的交易记录 (增强版表格)"""
        trades = self.saver.get_recent_trades(limit=10)
        if not trades:
            return
            
        print("\n" + "─"*100)
        print("📜 最近 10 次成交审计 (The Executor History)")
        print("─"*100)
        header = f"{'时间':<12} | {'币种':<8} | {'方向':<10} | {'成交价':<10} | {'成本':<10} | {'卖出价':<10} | {'盈亏':<10} | {'状态'}"
        print(header)
        print("─"*100)
        
        for t in trades:
            # 简化时间
            fmt_time = str(t.get('record_time', 'N/A'))[5:16]
            symbol = t.get('symbol', 'BTC')[:7]
            action = t.get('action', 'N/A')
            price = f"${float(t.get('price', 0)):,.1f}"
            cost = f"${float(t.get('cost', 0)):,.1f}"
            exit_p = f"${float(t.get('exit_price', 0)):,.1f}" if float(t.get('exit_price', 0)) > 0 else "-"
            
            pnl_val = float(t.get('pnl', 0))
            pnl_str = f"{'+' if pnl_val > 0 else ''}${pnl_val:,.2f}" if pnl_val != 0 else "-"
            
            status = t.get('status', 'N/A')
            
            row = f"{fmt_time:<12} | {symbol:<8} | {action:<10} | {price:<10} | {cost:<10} | {exit_p:<10} | {pnl_str:<10} | {status}"
            print(row)
        print("─"*100)
    
    def run_continuous(self, interval_minutes: int = 5):
        """
        持续运行交易机器人
        
        Args:
            interval_minutes: 检查间隔（分钟）
        """
        print(f"\n🔄 开始持续运行模式，间隔 {interval_minutes} 分钟...")
        
        try:
            while True:
                result = self.run_once()
                
                print(f"\n循环结果: {result['status']}")
                
                # 等待下一次检查
                print(f"\n⏳ 等待 {interval_minutes} 分钟...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  收到停止信号，退出...")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'decision_core': self.decision_core.get_statistics(),
            'risk_audit': self.risk_audit.get_audit_report(),
        }


# ============================================
# 主入口
# ============================================
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='多Agent交易机器人')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--max-position', type=float, default=100.0, help='最大单笔金额')
    parser.add_argument('--leverage', type=int, default=1, help='杠杆倍数')
    parser.add_argument('--stop-loss', type=float, default=1.0, help='止损百分比')
    parser.add_argument('--take-profit', type=float, default=2.0, help='止盈百分比')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='once', help='运行模式')
    parser.add_argument('--interval', type=int, default=5, help='持续运行间隔（分钟）')
    
    args = parser.parse_args()
    
    # 创建机器人
    bot = MultiAgentTradingBot(
        max_position_size=args.max_position,
        leverage=args.leverage,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        test_mode=args.test
    )
    
    # 运行
    if args.mode == 'once':
        result = bot.run_once()
        print(f"\n最终结果: {json.dumps(result, indent=2)}")
        
        # 显示统计
        stats = bot.get_statistics()
        print(f"\n统计信息:")
        print(json.dumps(stats, indent=2))
    else:
        bot.run_continuous(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
