#!/usr/bin/env python3
"""
项目清理脚本
识别并清理调试、测试和临时文件,使项目更加简洁
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# 工作区根目录
WORKSPACE_ROOT = Path(__file__).parent

# 文件分类规则
FILE_CATEGORIES = {
    "debug_scripts": [
        "debug_*.py",
        "diagnose_*.py",
        "analyze_*.py",
    ],
    "test_scripts": [
        "test_*.py",
        "verify_*.py",
    ],
    "temporary_files": [
        "*.backup",
        "*.broken",
        "*_old.*",
        "*_temp.*",
    ],
    "duplicate_docs": [
        "QUICK_REFERENCE.txt",
        "FIX_SUCCESS_SUMMARY.txt",
        "DATA_ARCHIVE_STATUS.txt",
        "VERIFICATION_REPORT.txt",
        "DOCS_ORGANIZATION_SUCCESS.txt",
    ],
    "redundant_scripts": [
        "run_live_trading_fixed.py",
        "run_live_simple.py",
        "run_strategy_live.py",
        "run_with_pipeline_logs.py",
        "run_with_detailed_logs.py",
        "run_plan_a.py",
        "simple_trade.py",
        "execute_real_trade.py",
        "test_single_trade.py",
        "test_real_trade.py",
        "set_sl_tp_manual.py",
        "transfer_funds.py",
        "migrate_data_structure.py",
    ],
    "utility_scripts": [
        "check_*.py",
        "view_*.py",
        "show_*.py",
        "create_*.py",
        "setup_*.py",
    ],
    "shell_scripts": [
        "*.sh",
    ],
}

# 需要保留的重要文件
KEEP_FILES = {
    # 核心运行脚本
    "main.py",
    "run_live_trading.py",
    
    # 配置和环境
    "requirements.txt",
    ".env.example",
    "config.example.yaml",
    ".gitignore",
    
    # 重要工具脚本
    "organize_docs.py",
    
    # 测试目录
    "tests/",
    
    # 源代码
    "src/",
    
    # 配置目录
    "config/",
    
    # 文档目录
    "docs/",
    "docs_organized/",
    
    # 研究目录
    "research/",
    
    # 数据目录
    "data/",
    "logs/",
    
    # 重要文档
    "DOCS_README.md",
    "DOCS_ORGANIZATION_REPORT.md",
    
    # 保留的 shell 脚本
    "set_api_keys.sh",
    "switch_to_production.sh",
}

def should_keep(file_path: Path) -> bool:
    """判断文件是否应该保留"""
    file_str = str(file_path.relative_to(WORKSPACE_ROOT))
    
    # 检查是否在保留列表中
    for keep_pattern in KEEP_FILES:
        if keep_pattern.endswith('/'):
            if file_str.startswith(keep_pattern) or f"/{keep_pattern}" in file_str:
                return True
        elif file_str == keep_pattern or file_str.endswith(f"/{keep_pattern}"):
            return True
    
    return False

def categorize_file(file_path: Path) -> str:
    """对文件进行分类"""
    import fnmatch
    
    filename = file_path.name
    
    for category, patterns in FILE_CATEGORIES.items():
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return category
    
    return "other"

def scan_project() -> Dict[str, List[Path]]:
    """扫描项目文件"""
    categorized_files = {
        "debug_scripts": [],
        "test_scripts": [],
        "temporary_files": [],
        "duplicate_docs": [],
        "redundant_scripts": [],
        "utility_scripts": [],
        "shell_scripts": [],
        "other": [],
    }
    
    # 扫描根目录的 Python 文件
    for file_path in WORKSPACE_ROOT.glob("*.py"):
        if file_path.name == "cleanup_project.py":
            continue
        if should_keep(file_path):
            continue
        
        category = categorize_file(file_path)
        categorized_files[category].append(file_path)
    
    # 扫描根目录的其他文件
    for pattern in ["*.txt", "*.backup", "*.broken", "*.sh", "*.yaml.backup"]:
        for file_path in WORKSPACE_ROOT.glob(pattern):
            if should_keep(file_path):
                continue
            
            category = categorize_file(file_path)
            categorized_files[category].append(file_path)
    
    return categorized_files

def create_archive_dir() -> Path:
    """创建归档目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = WORKSPACE_ROOT / f"archived_files_{timestamp}"
    archive_dir.mkdir(exist_ok=True)
    return archive_dir

def generate_report(categorized_files: Dict[str, List[Path]], action: str) -> str:
    """生成清理报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_files = sum(len(files) for files in categorized_files.values())
    
    report = f"""# 项目清理报告

**生成时间**: {timestamp}
**清理操作**: {action}

## 📊 清理统计

总文件数: {total_files}

"""
    
    for category, files in categorized_files.items():
        if not files:
            continue
        
        category_name = {
            "debug_scripts": "调试脚本",
            "test_scripts": "测试/验证脚本",
            "temporary_files": "临时文件",
            "duplicate_docs": "重复文档",
            "redundant_scripts": "冗余脚本",
            "utility_scripts": "工具脚本",
            "shell_scripts": "Shell 脚本",
            "other": "其他文件",
        }.get(category, category)
        
        report += f"\n### {category_name} ({len(files)} 个文件)\n\n"
        
        for file_path in sorted(files):
            file_size = file_path.stat().st_size / 1024  # KB
            report += f"- `{file_path.name}` ({file_size:.1f} KB)\n"
    
    report += f"""

## 📋 清理建议

### 🗑️ 可以删除的文件 (已归档)

**调试脚本** - 用于调试特定问题,已完成使命
**临时文件** - 备份和损坏文件
**重复文档** - 已整理到 docs_organized/

### 🔧 需要审查的文件

**测试脚本** - 部分测试脚本可能仍有用
**冗余脚本** - 功能已被 run_live_trading.py 取代
**工具脚本** - 部分可能仍需要用于维护

### ✅ 保留的核心文件

- `main.py` - 主程序入口
- `run_live_trading.py` - 实盘交易主脚本
- `requirements.txt` - 依赖管理
- `.env.example` - 环境配置模板
- `config.example.yaml` - 配置模板
- `src/` - 核心源代码
- `tests/` - 单元测试
- `docs_organized/` - 整理后的文档
- `DOCS_README.md` - 文档导航

## 🎯 清理后的项目结构

```
ai_trader/
├── src/                    # 核心源代码
│   ├── api/
│   ├── execution/
│   ├── features/
│   ├── monitoring/
│   ├── risk/
│   ├── strategy/
│   └── utils/
├── tests/                  # 单元测试
├── config/                 # 配置文件
├── docs_organized/         # 整理后的文档
├── research/               # 研究和回测
├── data/                   # 数据存储
├── logs/                   # 日志文件
├── main.py                 # 主程序
├── run_live_trading.py     # 实盘交易
├── requirements.txt        # 依赖
├── .env.example            # 环境变量模板
└── config.example.yaml     # 配置模板
```

## ⚠️ 注意事项

1. 所有文件已移动到归档目录,不是永久删除
2. 如需恢复,可从归档目录中找回
3. 建议审查归档文件后再考虑永久删除

---

*清理工具*: cleanup_project.py  
*归档位置*: archived_files_*
"""
    
    return report

def cleanup(dry_run: bool = True):
    """执行清理操作"""
    print("=" * 80)
    print("项目清理工具")
    print("=" * 80)
    
    # 扫描文件
    print("\n🔍 扫描项目文件...")
    categorized_files = scan_project()
    
    total_files = sum(len(files) for files in categorized_files.values())
    print(f"找到 {total_files} 个可清理的文件\n")
    
    # 显示分类统计
    for category, files in categorized_files.items():
        if files:
            category_name = {
                "debug_scripts": "调试脚本",
                "test_scripts": "测试/验证脚本",
                "temporary_files": "临时文件",
                "duplicate_docs": "重复文档",
                "redundant_scripts": "冗余脚本",
                "utility_scripts": "工具脚本",
                "shell_scripts": "Shell 脚本",
                "other": "其他文件",
            }.get(category, category)
            print(f"  {category_name}: {len(files)} 个文件")
    
    if dry_run:
        print("\n⚠️  这是预览模式,不会实际移动文件")
        print("要执行清理,请运行: python cleanup_project.py --execute")
    else:
        print("\n⚠️  将要移动文件到归档目录")
        confirm = input("确认执行清理? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ 清理已取消")
            return
        
        # 创建归档目录
        archive_dir = create_archive_dir()
        print(f"\n📁 创建归档目录: {archive_dir}")
        
        # 移动文件
        moved_count = 0
        for category, files in categorized_files.items():
            if not files:
                continue
            
            category_dir = archive_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for file_path in files:
                try:
                    dest = category_dir / file_path.name
                    shutil.move(str(file_path), str(dest))
                    print(f"  ✓ {file_path.name} -> {category}/")
                    moved_count += 1
                except Exception as e:
                    print(f"  ✗ 错误: {file_path.name} - {e}")
        
        print(f"\n✅ 已移动 {moved_count} 个文件到归档目录")
        
        # 生成报告
        report_path = archive_dir / "CLEANUP_REPORT.md"
        report = generate_report(categorized_files, "归档")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 清理报告: {report_path}")
    
    # 生成预览报告
    if dry_run:
        report = generate_report(categorized_files, "预览")
        preview_path = WORKSPACE_ROOT / "CLEANUP_PREVIEW.md"
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 预览报告已生成: {preview_path}")
    
    print("\n" + "=" * 80)
    print("清理完成!")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    dry_run = "--execute" not in sys.argv
    cleanup(dry_run=dry_run)
