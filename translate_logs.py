#!/usr/bin/env python3
"""
Batch replace Chinese log messages with English equivalents
"""

import re
import os

# Translation mapping: Chinese -> English
TRANSLATIONS = {
    # Agent initialization
    "预测预言家 (The Prophet) 初始化完成": "The Prophet initialized",
    "量化策略师 (The Strategist) 初始化完成": "The Strategist initialized",
    "数据先知 (The Oracle) 初始化完成": "The Oracle initialized",
    "风控守护者 (The Guardian) 初始化完成": "The Guardian initialized",
    
    # Common phrases
    "初始化完成": "initialized",
    "启动失败": "startup failed",
    "回退到": "falling back to",
    "初始数据加载完成": "Initial data loaded",
    "后续将使用": "will use",
    "缓存": "cache",
    "已完成": "completed",
    "实时": "live",
    "数据获取完成": "Data fetched",
    "耗时": "duration",
    "秒": "s",
    
    # Specific messages
    "预测周期": "Horizon",
    "币种": "Symbol",
    "模式": "Mode",
    "规则评分": "Rule-based scoring",
    
    # WebSocket
    "WebSocket 启动失败，回退到 REST API": "WebSocket startup failed, falling back to REST API",
    "✅ 初始数据加载完成，后续将使用 WebSocket 缓存": "✅ Initial data loaded, will use WebSocket cache",
}

def translate_file(filepath):
    """Translate Chinese logs in a file to English"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply translations
        for chinese, english in TRANSLATIONS.items():
            content = content.replace(chinese, english)
        
        # Additional pattern-based replacements
        # Pattern: f"🔮 预测预言家 (The Prophet) 初始化完成 | 预测周期: {horizon} | 币种: {symbol} | 模式: {mode_str}"
        content = re.sub(
            r'f"🔮 预测预言家 \(The Prophet\) 初始化完成 \| 预测周期: \{([^}]+)\} \| 币种: \{([^}]+)\} \| 模式: \{([^}]+)\}"',
            r'f"🔮 The Prophet initialized | Horizon: {\1} | Symbol: {\2} | Mode: {\3}"',
            content
        )
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {filepath}")
            return True
        else:
            print(f"⏭️  No changes: {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function"""
    files_to_process = [
        'src/agents/predict_agent.py',
        'src/agents/quant_analyst_agent.py',
        'src/agents/data_sync_agent.py',
        'src/agents/risk_audit_agent.py',
    ]
    
    updated_count = 0
    for filepath in files_to_process:
        if os.path.exists(filepath):
            if translate_file(filepath):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print(f"\n📊 Summary: {updated_count}/{len(files_to_process)} files updated")

if __name__ == '__main__':
    main()
