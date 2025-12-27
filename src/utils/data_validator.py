"""
Data Validator - Detect logical contradictions in market data

Validates consistency between:
- Bollinger Band position vs Price Position
- Agent output consensus (Trend vs Setup)
"""

from typing import List, Optional, Dict


class DataValidator:
    """Validates market data for logical consistency"""
    
    @staticmethod
    def check_bb_position_conflict(
        bb_lower: float,
        bb_upper: float,
        price: float,
        position_pct: float
    ) -> Optional[str]:
        """
        Check if BB breach contradicts position percentage
        
        Logic:
        - If price < bb_lower (breach), position should be < 10%
        - If price > bb_upper (breach), position should be > 90%
        
        Returns:
            Warning message if conflict detected, None otherwise
        """
        if price < bb_lower and position_pct > 10:
            return f"⚠️ DATA ANOMALY: Price ${price:.2f} below BB lower ${bb_lower:.2f} but position={position_pct:.1f}% (expected <10%)"
        
        if price > bb_upper and position_pct < 90:
            return f"⚠️ DATA ANOMALY: Price ${price:.2f} above BB upper ${bb_upper:.2f} but position={position_pct:.1f}% (expected >90%)"
        
        return None
    
    @staticmethod
    def check_agent_consensus(
        trend_stance: str,
        setup_analysis: str,
        trigger_analysis: str = ""
    ) -> List[str]:
        """
        Cross-validate agent outputs for contradictions
        
        Args:
            trend_stance: Trend Agent stance (UPTREND/DOWNTREND/NEUTRAL)
            setup_analysis: Setup Agent text analysis
            trigger_analysis: Trigger Agent text analysis
            
        Returns:
            List of conflict warnings
        """
        conflicts = []
        
        # Check Trend vs Setup alignment
        if 'DOWNTREND' in trend_stance.upper():
            if 'WAIT' in setup_analysis.upper() and 'DOWNTREND' not in setup_analysis.upper():
                conflicts.append("⚠️ AGENT CONFLICT: Trend Agent=DOWNTREND but Setup Agent suggests WAIT without bearish confirmation")
        
        if 'UPTREND' in trend_stance.upper():
            if 'WAIT' in setup_analysis.upper() and 'UPTREND' not in setup_analysis.upper():
                conflicts.append("⚠️ AGENT CONFLICT: Trend Agent=UPTREND but Setup Agent suggests WAIT without bullish confirmation")
        
        # Check for Setup Agent hallucinations
        if 'trend direction is' in setup_analysis.lower():
            # Setup Agent should not redefine trend direction
            conflicts.append("⚠️ AGENT HALLUCINATION: Setup Agent attempting to redefine trend direction (should defer to Trend Agent)")
        
        return conflicts
    
    @staticmethod
    def validate_market_data(market_data: Dict) -> Dict[str, List[str]]:
        """
        Comprehensive validation of market data
        
        Args:
            market_data: Dict containing price, BB, position, agent outputs
            
        Returns:
            Dict with 'anomalies' and 'conflicts' lists
        """
        anomalies = []
        conflicts = []
        
        # BB vs Position check
        if all(k in market_data for k in ['bb_lower', 'bb_upper', 'price', 'position_pct']):
            bb_conflict = DataValidator.check_bb_position_conflict(
                market_data['bb_lower'],
                market_data['bb_upper'],
                market_data['price'],
                market_data['position_pct']
            )
            if bb_conflict:
                anomalies.append(bb_conflict)
        
        # Agent consensus check
        if 'trend_stance' in market_data and 'setup_analysis' in market_data:
            agent_conflicts = DataValidator.check_agent_consensus(
                market_data['trend_stance'],
                market_data['setup_analysis'],
                market_data.get('trigger_analysis', '')
            )
            conflicts.extend(agent_conflicts)
        
        return {
            'anomalies': anomalies,
            'conflicts': conflicts,
            'has_issues': len(anomalies) + len(conflicts) > 0
        }
