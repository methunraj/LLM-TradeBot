#!/usr/bin/env python3
"""
分析和整理项目中的 Markdown 文档文件
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re


# 文档分类规则
DOC_CATEGORIES = {
    "01_快速开始": [
        "README.md",
        "QUICKSTART.md",
        "QUICK_START.md",
        "QUICKSTART_PLAN_A.md",
        "GETTING_STARTED.md",
        "INDEX.md",
        "PROJECT_INDEX.md",
    ],
    "02_配置指南": [
        "CONFIG_GUIDE.md",
        "API_KEYS_REFERENCE.md",
        "BINANCE_IP_WHITELIST_GUIDE.md",
        "ENV_CONFIG.md",
    ],
    "03_架构设计": [
        "ARCHITECTURE.md",
        "SYSTEM_SUMMARY.md",
        "PROJECT_SUMMARY.md",
        "FILE_MANIFEST.md",
    ],
    "04_工作流程": [
        "WORKFLOW_GUIDE.md",
        "STRATEGY_DEVELOPMENT_GUIDE.md",
        "QUICKSTART_PLAN_A.md",
    ],
    "05_数据管道": [
        "DATA_PIPELINE.md",
        "DATA_FLOW_SUMMARY.md",
        "DATA_FLOW_INDEX.md",
        "DATA_FLOW_COMPLETION_REPORT.md",
        "DATA_FLOW_FIX_SUMMARY.md",
        "DATA_PIPELINE_VERIFICATION.md",
        "DATA_SOURCE_MIGRATION_GUIDE.md",
        "DATA_MIGRATION_SUCCESS_REPORT.md",
        "DATA_QUALITY_FIX_REPORT.md",
        "QUICK_DATA_VERIFICATION.md",
    ],
    "06_日志系统": [
        "PIPELINE_LOG_GUIDE.md",
        "PIPELINE_LOG_INDEX.md",
        "PIPELINE_LOG_QUICKSTART.md",
        "PIPELINE_LOG_COMPLETE.md",
        "TRADE_LOGGING_GUIDE.md",
        "TRADE_LOGGING_COMPLETE.md",
        "LOGGER_USAGE_GUIDE.md",
        "LOG_JSON_ENHANCEMENT.md",
    ],
    "07_实盘交易": [
        "LIVE_TRADING_QUICKSTART.md",
        "LIVE_TRADING_READY.md",
        "LIVE_TRADING_SUCCESS.md",
        "LIVE_TRADING_USAGE.md",
        "LIVE_TRADING_SAFETY_GUIDE.md",
        "FUTURES_TRADING_FIX_REPORT.md",
        "STOP_LOSS_TAKE_PROFIT_GUIDE.md",
    ],
    "08_测试验证": [
        "TRADING_LOGIC_VERIFICATION_CHECKLIST.md",
        "TRADING_LOGIC_VERIFICATION_CHECKLIST_PRODUCTION.md",
        "SYSTEM_TEST_REPORT.md",
        "COLOR_TEST_REPORT.md",
    ],
    "09_项目报告": [
        "PROJECT_COMPLETION_REPORT.md",
        "PROJECT_RUN_SUCCESS_REPORT.md",
        "FINAL_SUCCESS_REPORT.md",
        "FINAL_SUMMARY.md",
        "PLAN_A_SUCCESS_REPORT.md",
        "PLAN_A_FINAL_SUMMARY.md",
        "PLAN_A_CHECKLIST.md",
        "PLAN2_READY.md",
        "SESSION_SUMMARY.md",
        "DEPLOYMENT_STATUS.md",
    ],
    "10_问题修复": [
        "BUG_FIX_REPORT.md",
        "FIX_REPORT.md",
        "PROBLEM_ANALYSIS_REPORT.md",
        "FORMAT_FIX.md",
        "COLOR_OPTIMIZATION.md",
        "DEEPSEEK_QUALITY_COMPARISON.md",
        "FEATURE_ENHANCEMENT.md",
    ],
    "11_检查清单": [
        "CHECKLIST.md",
    ],
    "12_其他": [],  # 未分类的文件
}


def analyze_md_file(file_path: Path) -> Dict:
    """分析单个 Markdown 文件"""
    info = {
        "name": file_path.name,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "lines": 0,
        "title": "",
        "category": None,
        "keywords": [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            info["lines"] = len(lines)
            
            # 提取标题（前10行中的第一个 # 标题）
            for i, line in enumerate(lines[:10]):
                if line.strip().startswith('#'):
                    info["title"] = line.strip().lstrip('#').strip()
                    break
            
            # 提取关键词（从标题和内容中）
            content = ' '.join(lines[:50])  # 前50行
            keywords = re.findall(r'\b[A-Z][A-Z_]+\b', content)
            info["keywords"] = list(set(keywords))[:10]
    
    except Exception as e:
        info["error"] = str(e)
    
    return info


def categorize_file(filename: str) -> str:
    """根据文件名分类"""
    for category, files in DOC_CATEGORIES.items():
        if filename in files:
            return category
    return "12_其他"


def organize_documents():
    """整理文档"""
    project_root = Path(__file__).parent
    docs_dir = project_root / "docs_organized"
    
    # 创建整理目录
    if docs_dir.exists():
        print(f"⚠️  目录已存在: {docs_dir}")
        response = input("是否删除并重新创建? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(docs_dir)
        else:
            print("取消操作")
            return
    
    docs_dir.mkdir(exist_ok=True)
    
    # 询问是否删除原文件
    print("\n⚠️  重要提示：文件复制后可以删除原文件")
    delete_original = input("是否在复制后删除原文件? (y/n): ").lower() == 'y'
    if delete_original:
        print("✅ 将在复制后删除原文件\n")
    else:
        print("✅ 将保留原文件\n")
    
    # 创建分类目录
    for category in DOC_CATEGORIES.keys():
        (docs_dir / category).mkdir(exist_ok=True)
    
    # 查找所有 .md 文件
    md_files = list(project_root.glob("*.md"))
    md_files.extend((project_root / "docs").glob("*.md"))
    
    print(f"\n找到 {len(md_files)} 个 Markdown 文件\n")
    
    # 分析并分类文件
    file_info_list = []
    category_counts = {cat: 0 for cat in DOC_CATEGORIES.keys()}
    
    for md_file in md_files:
        info = analyze_md_file(md_file)
        category = categorize_file(md_file.name)
        info["category"] = category
        category_counts[category] += 1
        file_info_list.append(info)
        
        # 复制文件到对应分类目录
        dest_dir = docs_dir / category
        dest_file = dest_dir / md_file.name
        
        # 如果目标文件已存在，添加序号
        if dest_file.exists():
            base_name = md_file.stem
            ext = md_file.suffix
            counter = 1
            while dest_file.exists():
                dest_file = dest_dir / f"{base_name}_{counter}{ext}"
                counter += 1
        
        shutil.copy2(md_file, dest_file)
        
        # 如果用户选择删除原文件，则删除
        if delete_original:
            try:
                md_file.unlink()
                print(f"  ✅ {md_file.name} -> {category}/ (已删除原文件)")
            except Exception as e:
                print(f"  ⚠️  {md_file.name} -> {category}/ (复制成功，但删除原文件失败: {e})")
        else:
            print(f"  ✅ {md_file.name} -> {category}/")
    
    # 生成索引文件
    generate_index(docs_dir, file_info_list, category_counts)
    
    # 生成分类统计
    generate_summary(docs_dir, file_info_list, category_counts)
    
    print(f"\n✅ 文档整理完成！")
    print(f"📁 整理目录: {docs_dir}")
    print(f"\n📊 分类统计:")
    for category, count in sorted(category_counts.items()):
        if count > 0:
            print(f"  {category}: {count} 个文件")


def generate_index(docs_dir: Path, file_info_list: List[Dict], category_counts: Dict):
    """生成索引文件"""
    index_content = """# 📚 项目文档索引

本文档索引提供了项目中所有 Markdown 文档的完整列表和分类。

## 📊 文档统计

"""
    
    total_files = len(file_info_list)
    total_categories = sum(1 for count in category_counts.values() if count > 0)
    
    index_content += f"- **总文件数**: {total_files}\n"
    index_content += f"- **分类数**: {total_categories}\n"
    index_content += f"- **生成时间**: {Path(__file__).stat().st_mtime}\n\n"
    
    index_content += "## 📁 分类目录\n\n"
    
    for category in sorted(DOC_CATEGORIES.keys()):
        count = category_counts[category]
        if count == 0:
            continue
        
        category_name = category.replace('_', ' ').replace('0', '').strip()
        index_content += f"### {category_name} ({count} 个文件)\n\n"
        
        files_in_category = [f for f in file_info_list if f["category"] == category]
        for file_info in sorted(files_in_category, key=lambda x: x["name"]):
            title = file_info.get("title", file_info["name"])
            size_kb = file_info["size"] / 1024
            lines = file_info["lines"]
            
            index_content += f"- **[{file_info['name']}]({category}/{file_info['name']})**\n"
            index_content += f"  - 标题: {title}\n"
            index_content += f"  - 大小: {size_kb:.1f} KB\n"
            index_content += f"  - 行数: {lines}\n"
            if file_info.get("keywords"):
                keywords_str = ", ".join(file_info["keywords"][:5])
                index_content += f"  - 关键词: {keywords_str}\n"
            index_content += "\n"
    
    # 写入索引文件
    index_file = docs_dir / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"\n  ✅ 生成索引文件: {index_file}")


def generate_summary(docs_dir: Path, file_info_list: List[Dict], category_counts: Dict):
    """生成分类摘要"""
    summary_content = """# 📋 文档分类摘要

本文档提供了各分类的简要说明和文件列表。

"""
    
    category_descriptions = {
        "01_快速开始": "快速入门指南，帮助新用户快速上手项目",
        "02_配置指南": "配置相关的文档，包括API密钥、环境配置等",
        "03_架构设计": "系统架构和设计文档",
        "04_工作流程": "工作流程和策略开发指南",
        "05_数据管道": "数据流转、处理和质量相关的文档",
        "06_日志系统": "日志记录和使用指南",
        "07_实盘交易": "实盘交易相关的指南和报告",
        "08_测试验证": "测试和验证相关的文档",
        "09_项目报告": "项目完成报告和总结",
        "10_问题修复": "问题分析和修复报告",
        "11_检查清单": "各种检查清单",
        "12_其他": "未分类的文档",
    }
    
    for category in sorted(DOC_CATEGORIES.keys()):
        count = category_counts[category]
        if count == 0:
            continue
        
        category_name = category.replace('_', ' ').replace('0', '').strip()
        description = category_descriptions.get(category, "无描述")
        
        summary_content += f"## {category_name}\n\n"
        summary_content += f"**说明**: {description}\n\n"
        summary_content += f"**文件数**: {count}\n\n"
        
        files_in_category = [f for f in file_info_list if f["category"] == category]
        summary_content += "**文件列表**:\n\n"
        for file_info in sorted(files_in_category, key=lambda x: x["name"]):
            title = file_info.get("title", file_info["name"])
            summary_content += f"- [{file_info['name']}]({category}/{file_info['name']}) - {title}\n"
        
        summary_content += "\n---\n\n"
    
    # 写入摘要文件
    summary_file = docs_dir / "SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"  ✅ 生成摘要文件: {summary_file}")


if __name__ == "__main__":
    organize_documents()

