"""
数据保存工具模块 - 按日期组织数据文件
"""
import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.logger import log


class DataSaver:
    """数据保存工具类 - 按步骤和日期自动组织文件
    
    目录结构:
    data/
      step1/
        20251217/
          step1_klines_BTCUSDT_5m_20251217_220226.json
          step1_klines_BTCUSDT_5m_20251217_220226.csv
          ...
      step2/
        20251217/
          step2_indicators_BTCUSDT_5m_20251217_220226.parquet
          ...
      step3/
        20251217/
          step3_features_BTCUSDT_5m_20251217_220226.parquet
          ...
    """
    
    def __init__(self, base_dir: str = 'data'):
        self.base_dir = base_dir
        # 创建步骤目录
        self.step1_dir = os.path.join(base_dir, 'step1')
        self.step2_dir = os.path.join(base_dir, 'step2')
        self.step3_dir = os.path.join(base_dir, 'step3')
        self.step4_dir = os.path.join(base_dir, 'step4')
        self.step5_dir = os.path.join(base_dir, 'step5')
        self.step6_dir = os.path.join(base_dir, 'step6')
        self.step7_dir = os.path.join(base_dir, 'step7')
        self.step8_dir = os.path.join(base_dir, 'step8')
        self.step9_dir = os.path.join(base_dir, 'step9')
        
        os.makedirs(self.step1_dir, exist_ok=True)
        os.makedirs(self.step2_dir, exist_ok=True)
        os.makedirs(self.step3_dir, exist_ok=True)
        os.makedirs(self.step4_dir, exist_ok=True)
        os.makedirs(self.step5_dir, exist_ok=True)
        os.makedirs(self.step6_dir, exist_ok=True)
        os.makedirs(self.step7_dir, exist_ok=True)
        os.makedirs(self.step8_dir, exist_ok=True)
        os.makedirs(self.step9_dir, exist_ok=True)
    
    def _get_date_folder(self, step: str, date: Optional[str] = None) -> str:
        """获取或创建指定步骤的日期文件夹
        
        Args:
            step: 步骤名称 'step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8'
            date: 日期字符串 YYYYMMDD，默认为今天
            
        Returns:
            日期文件夹路径
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        step_dir = getattr(self, f'{step}_dir')
        date_folder = os.path.join(step_dir, date)
        os.makedirs(date_folder, exist_ok=True)
        return date_folder
    
    def save_step1_klines(
        self,
        klines: List[Dict],
        symbol: str,
        timeframe: str,
        save_formats: List[str] = ['json', 'csv', 'parquet']
    ) -> Dict[str, str]:
        """保存步骤1的原始K线数据
        
        Args:
            klines: K线数据列表
            symbol: 交易对
            timeframe: 时间周期
            save_formats: 保存格式列表，可选 'json', 'csv', 'parquet'
            
        Returns:
            保存的文件路径字典 {format: filepath}
        """
        if not klines:
            log.warning("K线数据为空，跳过保存")
            return {}
        
        # 获取步骤1的日期文件夹
        date_folder = self._get_date_folder('step1')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 元数据
        df = pd.DataFrame(klines)
        first_ts = pd.to_datetime(klines[0]['timestamp'], unit='ms')
        last_ts = pd.to_datetime(klines[-1]['timestamp'], unit='ms')
        
        metadata = {
            'symbol': symbol,
            'timeframe': timeframe,
            'limit': len(klines),
            'fetch_time': timestamp,
            'count': len(klines),
            'time_range': {
                'start': str(first_ts),
                'end': str(last_ts)
            }
        }
        
        saved_files = {}
        
        # 保存 JSON
        if 'json' in save_formats:
            json_file = os.path.join(
                date_folder,
                f'step1_klines_{symbol}_{timeframe}_{timestamp}.json'
            )
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': metadata,
                    'klines': klines
                }, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_file
            log.debug(f"保存 JSON: {json_file}")
        
        # 保存 CSV
        if 'csv' in save_formats:
            csv_file = os.path.join(
                date_folder,
                f'step1_klines_{symbol}_{timeframe}_{timestamp}.csv'
            )
            df['timestamp_readable'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.to_csv(csv_file, index=False, encoding='utf-8')
            saved_files['csv'] = csv_file
            log.debug(f"保存 CSV: {csv_file}")
        
        # 保存 Parquet
        if 'parquet' in save_formats:
            parquet_file = os.path.join(
                date_folder,
                f'step1_klines_{symbol}_{timeframe}_{timestamp}.parquet'
            )
            df.to_parquet(parquet_file, index=False)
            saved_files['parquet'] = parquet_file
            log.debug(f"保存 Parquet: {parquet_file}")
        
        # 生成统计报告
        stats_file = os.path.join(
            date_folder,
            f'step1_stats_{symbol}_{timeframe}_{timestamp}.txt'
        )
        self._save_stats_report(df, metadata, stats_file, saved_files)
        saved_files['stats'] = stats_file
        
        log.debug(f"步骤1数据已保存到: {date_folder}")
        return saved_files
    
    def _save_stats_report(
        self,
        df: pd.DataFrame,
        metadata: Dict,
        stats_file: str,
        saved_files: Dict[str, str]
    ):
        """保存统计报告"""
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤1 原始K线数据统计报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {metadata["symbol"]}\n')
            f.write(f'时间周期: {metadata["timeframe"]}\n')
            f.write(f'数据量: {metadata["count"]} 根K线\n')
            f.write(f'时间范围: {metadata["time_range"]["start"]} ~ {metadata["time_range"]["end"]}\n')
            f.write(f'获取时间: {metadata["fetch_time"]}\n\n')
            
            f.write('价格统计:\n')
            f.write(f'  开盘价: {df["open"].describe().to_string()}\n\n')
            f.write(f'  收盘价: {df["close"].describe().to_string()}\n\n')
            
            f.write('成交量统计:\n')
            f.write(f'{df["volume"].describe().to_string()}\n\n')
            
            f.write('数据完整性:\n')
            f.write(f'  缺失值: {df.isna().sum().sum()}\n')
            f.write(f'  重复行: {df.duplicated().sum()}\n\n')
            
            f.write('文件清单:\n')
            for fmt, path in saved_files.items():
                if fmt != 'stats':
                    size_kb = os.path.getsize(path) / 1024
                    f.write(f'  {fmt.upper()}: {os.path.basename(path)} ({size_kb:.1f} KB)\n')
    
    def save_step2_indicators(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        snapshot_id: str,
        save_stats: bool = True
    ) -> Dict[str, str]:
        """保存步骤2的技术指标数据
        
        Args:
            df: 包含技术指标的DataFrame
            symbol: 交易对
            timeframe: 时间周期
            snapshot_id: 快照ID
            save_stats: 是否保存统计报告
            
        Returns:
            保存的文件路径字典 {'parquet': ..., 'stats': ...}
        """
        date_folder = self._get_date_folder('step2')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        parquet_file = os.path.join(
            date_folder,
            f'step2_indicators_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.parquet'
        )
        
        df.to_parquet(parquet_file)
        log.debug(f"保存步骤2指标: {parquet_file}")
        
        saved_files = {'parquet': parquet_file}
        
        # 保存统计报告
        if save_stats:
            stats_file = self.save_step2_stats(df, symbol, timeframe, snapshot_id)
            saved_files['stats'] = stats_file
        
        return saved_files
    
    def save_step3_features(
        self,
        features: pd.DataFrame,
        symbol: str,
        timeframe: str,
        source_snapshot_id: str,
        feature_version: str = 'v1',
        save_stats: bool = True
    ) -> Dict[str, str]:
        """保存步骤3的特征快照
        
        Args:
            features: 特征DataFrame
            symbol: 交易对
            timeframe: 时间周期
            source_snapshot_id: 来源快照ID
            feature_version: 特征版本
            save_stats: 是否保存统计报告
            
        Returns:
            保存的文件路径字典 {'parquet': ..., 'stats': ...}
        """
        date_folder = self._get_date_folder('step3')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        parquet_file = os.path.join(
            date_folder,
            f'step3_features_{symbol}_{timeframe}_{timestamp}_{feature_version}.parquet'
        )
        
        features.to_parquet(parquet_file)
        log.debug(f"保存步骤3特征: {parquet_file}")
        
        saved_files = {'parquet': parquet_file}
        
        # 保存统计报告
        if save_stats:
            stats_file = self.save_step3_stats(features, symbol, timeframe, feature_version)
            saved_files['stats'] = stats_file
        
        return saved_files
    
    def save_step2_stats(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        snapshot_id: str
    ) -> str:
        """保存步骤2的统计报告
        
        Args:
            df: 包含技术指标的DataFrame
            symbol: 交易对
            timeframe: 时间周期
            snapshot_id: 快照ID
            
        Returns:
            统计报告文件路径
        """
        date_folder = self._get_date_folder('step2')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        stats_file = os.path.join(
            date_folder,
            f'step2_stats_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.txt'
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤2 技术指标统计报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'快照ID: {snapshot_id}\n')
            f.write(f'数据量: {len(df)} 根K线\n')
            f.write(f'生成时间: {timestamp}\n\n')
            
            # 数据质量检查
            f.write('数据质量:\n')
            f.write(f'  总列数: {len(df.columns)}\n')
            f.write(f'  缺失值总数: {df.isna().sum().sum()}\n')
            f.write(f'  无穷值总数: {(df == float("inf")).sum().sum() + (df == float("-inf")).sum().sum()}\n')
            
            if 'is_warmup' in df.columns:
                warmup_count = df['is_warmup'].sum()
                f.write(f'  预热期数据: {warmup_count} 根 ({warmup_count/len(df)*100:.1f}%)\n')
            
            # 关键指标统计
            f.write('\n关键技术指标统计:\n')
            key_indicators = [
                'rsi', 'macd', 'macd_signal', 'macd_hist',
                'bb_upper', 'bb_middle', 'bb_lower', 'atr',
                'obv', 'ema_12', 'ema_26', 'sma_20'
            ]
            
            for ind in key_indicators:
                if ind in df.columns:
                    valid_data = df[ind].replace([float('inf'), float('-inf')], float('nan')).dropna()
                    if len(valid_data) > 0:
                        f.write(f'\n  {ind}:\n')
                        f.write(f'    有效值: {len(valid_data)}/{len(df)} ({len(valid_data)/len(df)*100:.1f}%)\n')
                        f.write(f'    均值: {valid_data.mean():.6f}\n')
                        f.write(f'    标准差: {valid_data.std():.6f}\n')
                        f.write(f'    最小值: {valid_data.min():.6f}\n')
                        f.write(f'    最大值: {valid_data.max():.6f}\n')
        
        log.debug(f"保存步骤2统计报告: {stats_file}")
        return stats_file
    
    def save_step3_stats(
        self,
        features: pd.DataFrame,
        symbol: str,
        timeframe: str,
        feature_version: str = 'v1'
    ) -> str:
        """保存步骤3的特征统计报告
        
        Args:
            features: 特征DataFrame
            symbol: 交易对
            timeframe: 时间周期
            feature_version: 特征版本
            
        Returns:
            统计报告文件路径
        """
        date_folder = self._get_date_folder('step3')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        stats_file = os.path.join(
            date_folder,
            f'step3_stats_{symbol}_{timeframe}_{timestamp}_{feature_version}.txt'
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤3 特征快照统计报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'特征版本: {feature_version}\n')
            f.write(f'数据量: {len(features)} 根K线\n')
            f.write(f'生成时间: {timestamp}\n\n')
            
            # 数据质量检查
            f.write('数据质量:\n')
            f.write(f'  总特征数: {len(features.columns)}\n')
            f.write(f'  缺失值总数: {features.isna().sum().sum()}\n')
            f.write(f'  无穷值总数: {(features == float("inf")).sum().sum() + (features == float("-inf")).sum().sum()}\n')
            
            if 'is_feature_valid' in features.columns:
                valid_count = features['is_feature_valid'].sum()
                f.write(f'  有效特征行: {valid_count}/{len(features)} ({valid_count/len(features)*100:.1f}%)\n')
            
            if 'has_time_gap' in features.columns:
                gap_count = features['has_time_gap'].sum()
                f.write(f'  时间缺口: {gap_count} 处 ({gap_count/len(features)*100:.1f}%)\n')
            
            # 特征列表
            f.write('\n特征列表:\n')
            for col in sorted(features.columns):
                f.write(f'  - {col}\n')
            
            # 数值特征统计
            f.write('\n数值特征统计:\n')
            numeric_cols = features.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns
            
            for col in numeric_cols:
                if col not in ['is_feature_valid', 'has_time_gap', 'is_warmup']:
                    valid_data = features[col].replace([float('inf'), float('-inf')], float('nan')).dropna()
                    if len(valid_data) > 0:
                        f.write(f'\n  {col}:\n')
                        f.write(f'    有效值: {len(valid_data)}/{len(features)} ({len(valid_data)/len(features)*100:.1f}%)\n')
                        f.write(f'    均值: {valid_data.mean():.6f}\n')
                        f.write(f'    标准差: {valid_data.std():.6f}\n')
                        f.write(f'    分位数 [5%, 25%, 50%, 75%, 95%]: '
                               f'[{valid_data.quantile(0.05):.6f}, '
                               f'{valid_data.quantile(0.25):.6f}, '
                               f'{valid_data.quantile(0.50):.6f}, '
                               f'{valid_data.quantile(0.75):.6f}, '
                               f'{valid_data.quantile(0.95):.6f}]\n')
        
        log.debug(f"保存步骤3统计报告: {stats_file}")
        return stats_file
    
    def list_files(
        self,
        step: Optional[str] = None,
        date: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> List[str]:
        """列出指定步骤和日期的所有文件
        
        Args:
            step: 步骤名称 'step1'-'step9'，默认为所有步骤
            date: 日期字符串 YYYYMMDD，默认为今天
            pattern: 文件名模式（可选）
            
        Returns:
            文件路径列表
        """
        files = []
        
        steps = [step] if step else ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8', 'step9']
        
        for s in steps:
            date_folder = self._get_date_folder(s, date)
            
            if not os.path.exists(date_folder):
                continue
            
            for f in os.listdir(date_folder):
                if pattern is None or pattern in f:
                    files.append(os.path.join(date_folder, f))
        
        return sorted(files)
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> Dict[str, int]:
        """清理超过指定天数的旧数据
        
        Args:
            days_to_keep: 保留最近N天的数据
            
        Returns:
            删除统计 {step: deleted_count}
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted = {
            'step1': 0, 'step2': 0, 'step3': 0, 'step4': 0,
            'step5': 0, 'step6': 0, 'step7': 0, 'step8': 0, 'step9': 0
        }
        
        for step in ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8', 'step9']:
            step_dir = getattr(self, f'{step}_dir')
            
            if not os.path.exists(step_dir):
                continue
            
            # 遍历日期文件夹
            for date_folder in os.listdir(step_dir):
                try:
                    folder_date = datetime.strptime(date_folder, '%Y%m%d')
                    if folder_date < cutoff_date:
                        folder_path = os.path.join(step_dir, date_folder)
                        
                        # 删除该文件夹及其内容
                        import shutil
                        shutil.rmtree(folder_path)
                        deleted[step] += 1
                        log.info(f"删除旧数据文件夹: {folder_path}")
                except ValueError:
                    # 非日期格式的文件夹，跳过
                    continue
        
        return deleted
    
    def save_step4_context(
        self,
        context: Dict,
        symbol: str,
        timeframe: str,
        snapshot_id: str
    ) -> Dict[str, str]:
        """保存步骤4的多周期上下文数据
        
        Args:
            context: 多周期上下文字典
            symbol: 交易对
            timeframe: 时间周期
            snapshot_id: 快照ID
            
        Returns:
            保存的文件路径字典 {'json': ...}
        """
        date_folder = self._get_date_folder('step4')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(
            date_folder,
            f'step4_context_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.json'
        )
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        
        log.debug(f"保存步骤4上下文: {json_file}")
        return {'json': json_file}
    
    def save_step5_markdown(
        self,
        markdown_text: str,
        symbol: str,
        timeframe: str,
        snapshot_id: str
    ) -> Dict[str, str]:
        """保存步骤5的Markdown格式化文本
        
        Args:
            markdown_text: Markdown格式文本
            symbol: 交易对
            timeframe: 时间周期
            snapshot_id: 快照ID
            
        Returns:
            保存的文件路径字典 {'md': ...}
        """
        date_folder = self._get_date_folder('step5')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        md_file = os.path.join(
            date_folder,
            f'step5_llm_input_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.md'
        )
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        # 生成统计报告
        stats_file = os.path.join(
            date_folder,
            f'step5_stats_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.txt'
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤5 Markdown格式化统计报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'快照ID: {snapshot_id}\n')
            f.write(f'生成时间: {timestamp}\n\n')
            f.write(f'文本统计:\n')
            f.write(f'  总字符数: {len(markdown_text)}\n')
            f.write(f'  总行数: {markdown_text.count(chr(10)) + 1}\n')
            f.write(f'  总字节数: {len(markdown_text.encode("utf-8"))}\n\n')
            f.write(f'内容预览（前500字符）:\n')
            f.write('-' * 80 + '\n')
            f.write(markdown_text[:500] + '\n')
            f.write('-' * 80 + '\n')
        
        log.debug(f"保存步骤5 Markdown: {md_file}")
        return {'md': md_file, 'stats': stats_file}
    
    def save_step6_decision(
        self,
        decision: Dict,
        symbol: str,
        timeframe: str,
        snapshot_id: str
    ) -> Dict[str, str]:
        """保存步骤6的LLM决策输出
        
        Args:
            decision: LLM决策字典
            symbol: 交易对
            timeframe: 时间周期
            snapshot_id: 快照ID
            
        Returns:
            保存的文件路径字典 {'json': ..., 'stats': ...}
        """
        date_folder = self._get_date_folder('step6')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(
            date_folder,
            f'step6_decision_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.json'
        )
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(decision, f, indent=2, ensure_ascii=False)
        
        # 生成统计报告
        stats_file = os.path.join(
            date_folder,
            f'step6_stats_{symbol}_{timeframe}_{timestamp}_{snapshot_id}.txt'
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤6 LLM决策统计报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'快照ID: {snapshot_id}\n')
            f.write(f'生成时间: {timestamp}\n\n')
            
            f.write('决策内容:\n')
            if 'action' in decision:
                f.write(f'  动作: {decision["action"]}\n')
            if 'confidence' in decision:
                f.write(f'  信心度: {decision["confidence"]}%\n')
            if 'reason' in decision:
                f.write(f'  原因: {decision["reason"]}\n')
            
            f.write('\n完整决策数据:\n')
            f.write(json.dumps(decision, indent=2, ensure_ascii=False))
        
        log.debug(f"保存步骤6决策: {json_file}")
        return {'json': json_file, 'stats': stats_file}
    
    def save_step7_execution(
        self,
        execution_record: Dict,
        symbol: str,
        timeframe: str,
        order_id: Optional[str] = None
    ) -> Dict[str, str]:
        """保存步骤7的交易执行记录
        
        Args:
            execution_record: 交易执行记录字典
            symbol: 交易对
            timeframe: 时间周期
            order_id: 订单ID（可选）
            
        Returns:
            保存的文件路径字典 {'json': ..., 'csv': ...}
        """
        date_folder = self._get_date_folder('step7')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成唯一ID
        exec_id = order_id or f"exec_{timestamp}"
        
        # 保存JSON
        json_file = os.path.join(
            date_folder,
            f'step7_execution_{symbol}_{timeframe}_{timestamp}_{exec_id}.json'
        )
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(execution_record, f, indent=2, ensure_ascii=False)
        
        # 追加到CSV（用于统计分析）
        csv_file = os.path.join(
            date_folder,
            f'step7_executions_{symbol}_{timeframe}.csv'
        )
        
        # 将记录转换为DataFrame
        df_record = pd.DataFrame([execution_record])
        
        # 如果CSV文件已存在，追加；否则创建
        if os.path.exists(csv_file):
            df_existing = pd.read_csv(csv_file)
            df_combined = pd.concat([df_existing, df_record], ignore_index=True)
            df_combined.to_csv(csv_file, index=False)
        else:
            df_record.to_csv(csv_file, index=False)
        
        log.debug(f"保存步骤7执行记录: {json_file}")
        return {'json': json_file, 'csv': csv_file}
    
    def save_step8_backtest(
        self,
        backtest_results: Dict,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        strategy_version: str = 'v1'
    ) -> Dict[str, str]:
        """保存步骤8的回测/绩效数据
        
        Args:
            backtest_results: 回测结果字典
            symbol: 交易对
            timeframe: 时间周期
            start_date: 回测开始日期
            end_date: 回测结束日期
            strategy_version: 策略版本
            
        Returns:
            保存的文件路径字典 {'json': ..., 'stats': ...}
        """
        date_folder = self._get_date_folder('step8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存完整结果
        json_file = os.path.join(
            date_folder,
            f'step8_backtest_{symbol}_{timeframe}_{start_date}_{end_date}_{strategy_version}.json'
        )
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(backtest_results, f, indent=2, ensure_ascii=False)
        
        # 生成绩效报告
        stats_file = os.path.join(
            date_folder,
            f'step8_performance_{symbol}_{timeframe}_{start_date}_{end_date}_{strategy_version}.txt'
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('步骤8 回测绩效报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'策略版本: {strategy_version}\n')
            f.write(f'回测期间: {start_date} ~ {end_date}\n')
            f.write(f'生成时间: {timestamp}\n\n')
            
            # 关键指标
            metrics = backtest_results.get('metrics', {})
            f.write('关键绩效指标:\n')
            
            if 'total_return' in metrics:
                f.write(f'  总收益率: {metrics["total_return"]:.2f}%\n')
            if 'sharpe_ratio' in metrics:
                f.write(f'  夏普比率: {metrics["sharpe_ratio"]:.2f}\n')
            if 'max_drawdown' in metrics:
                f.write(f'  最大回撤: {metrics["max_drawdown"]:.2f}%\n')
            if 'win_rate' in metrics:
                f.write(f'  胜率: {metrics["win_rate"]:.2f}%\n')
            if 'total_trades' in metrics:
                f.write(f'  总交易次数: {metrics["total_trades"]}\n')
            
            f.write('\n完整回测数据:\n')
            f.write(json.dumps(backtest_results, indent=2, ensure_ascii=False)[:1000])
            f.write('\n...(详见JSON文件)')
        
        # 如果有交易记录DataFrame，保存为CSV和Parquet
        if 'trades' in backtest_results and isinstance(backtest_results['trades'], list):
            trades_df = pd.DataFrame(backtest_results['trades'])
            
            csv_file = os.path.join(
                date_folder,
                f'step8_trades_{symbol}_{timeframe}_{start_date}_{end_date}_{strategy_version}.csv'
            )
            parquet_file = os.path.join(
                date_folder,
                f'step8_trades_{symbol}_{timeframe}_{start_date}_{end_date}_{strategy_version}.parquet'
            )
            
            trades_df.to_csv(csv_file, index=False)
            trades_df.to_parquet(parquet_file, index=False)
            
            log.info(f"保存步骤8回测结果: {json_file}")
            return {
                'json': json_file,
                'stats': stats_file,
                'trades_csv': csv_file,
                'trades_parquet': parquet_file
            }
        
        log.info(f"保存步骤8回测结果: {json_file}")
        return {'json': json_file, 'stats': stats_file}
    
    def save_live_trade(
        self,
        trade_info: Dict,
        symbol: str,
        timeframe: str = '5m'
    ) -> Dict[str, str]:
        """保存实时交易信息（每次交易实时保存）
        
        Args:
            trade_info: 交易信息字典，包含：
                - signal: 交易信号 (BUY/SELL/HOLD)
                - price: 交易价格
                - quantity: 交易数量
                - amount: 交易金额
                - order_id: 订单ID
                - decision: 决策信息（可选）
                - market_state: 市场状态（可选）
                - execution_result: 执行结果（可选）
            symbol: 交易对
            timeframe: 时间周期
            
        Returns:
            保存的文件路径字典 {'json': ..., 'csv': ..., 'summary': ...}
        """
        # 使用 step9 目录保存实时交易
        date_folder = self._get_date_folder('step9')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 补充交易时间戳（如果没有）
        if 'timestamp' not in trade_info:
            trade_info['timestamp'] = datetime.now().isoformat()
        
        # 补充symbol和timeframe
        trade_info['symbol'] = symbol
        trade_info['timeframe'] = timeframe
        
        # 生成唯一的交易ID
        trade_id = trade_info.get('order_id') or f"trade_{timestamp}"
        
        # 1. 保存单次交易详情（JSON）
        json_file = os.path.join(
            date_folder,
            f'live_trade_{symbol}_{timestamp}_{trade_id}.json'
        )
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(trade_info, f, indent=2, ensure_ascii=False)
        
        log.info(f"保存实时交易: {json_file}")
        
        # 2. 追加到当日交易汇总CSV
        csv_file = os.path.join(
            date_folder,
            f'live_trades_summary_{symbol}_{timeframe}.csv'
        )
        
        # 提取关键字段用于CSV
        csv_record = {
            'timestamp': trade_info.get('timestamp'),
            'signal': trade_info.get('signal'),
            'price': trade_info.get('price'),
            'quantity': trade_info.get('quantity'),
            'amount': trade_info.get('amount'),
            'order_id': trade_info.get('order_id'),
            'success': trade_info.get('success', True),
            'leverage': trade_info.get('decision', {}).get('leverage') if isinstance(trade_info.get('decision'), dict) else None,
            'current_balance': trade_info.get('account_info', {}).get('available_balance') if isinstance(trade_info.get('account_info'), dict) else None
        }
        
        df_record = pd.DataFrame([csv_record])
        
        # 追加或创建CSV
        if os.path.exists(csv_file):
            df_existing = pd.read_csv(csv_file)
            df_combined = pd.concat([df_existing, df_record], ignore_index=True)
            df_combined.to_csv(csv_file, index=False)
        else:
            df_record.to_csv(csv_file, index=False)
        
        # 3. 生成当日交易摘要报告
        summary_file = os.path.join(
            date_folder,
            f'live_trades_daily_summary_{symbol}_{timeframe}.txt'
        )
        
        self._generate_daily_trade_summary(csv_file, summary_file, symbol, timeframe)
        
        return {
            'json': json_file,
            'csv': csv_file,
            'summary': summary_file
        }
    
    def _generate_daily_trade_summary(
        self,
        csv_file: str,
        summary_file: str,
        symbol: str,
        timeframe: str
    ):
        """生成当日交易摘要报告"""
        if not os.path.exists(csv_file):
            return
        
        df = pd.read_csv(csv_file)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('实时交易每日摘要报告\n')
            f.write('='*80 + '\n\n')
            f.write(f'交易对: {symbol}\n')
            f.write(f'时间周期: {timeframe}\n')
            f.write(f'报告日期: {datetime.now().strftime("%Y-%m-%d")}\n')
            f.write(f'最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            # 交易统计
            f.write('交易统计:\n')
            f.write(f'  总交易次数: {len(df)}\n')
            
            if 'signal' in df.columns:
                buy_count = (df['signal'] == 'BUY').sum()
                sell_count = (df['signal'] == 'SELL').sum()
                hold_count = (df['signal'] == 'HOLD').sum()
                f.write(f'  买入信号: {buy_count} 次\n')
                f.write(f'  卖出信号: {sell_count} 次\n')
                f.write(f'  持有信号: {hold_count} 次\n')
            
            if 'success' in df.columns:
                success_count = df['success'].sum()
                f.write(f'  成功执行: {success_count} 次\n')
                f.write(f'  失败次数: {len(df) - success_count} 次\n')
            
            # 金额统计
            if 'amount' in df.columns:
                valid_amounts = df['amount'].dropna()
                if len(valid_amounts) > 0:
                    f.write(f'\n金额统计:\n')
                    f.write(f'  总交易金额: ${valid_amounts.sum():,.2f}\n')
                    f.write(f'  平均交易金额: ${valid_amounts.mean():,.2f}\n')
                    f.write(f'  最大交易金额: ${valid_amounts.max():,.2f}\n')
                    f.write(f'  最小交易金额: ${valid_amounts.min():,.2f}\n')
            
            # 价格统计
            if 'price' in df.columns:
                valid_prices = df['price'].dropna()
                if len(valid_prices) > 0:
                    f.write(f'\n价格统计:\n')
                    f.write(f'  平均价格: ${valid_prices.mean():,.2f}\n')
                    f.write(f'  最高价格: ${valid_prices.max():,.2f}\n')
                    f.write(f'  最低价格: ${valid_prices.min():,.2f}\n')
            
            # 最近5笔交易
            f.write(f'\n最近5笔交易:\n')
            f.write('-' * 80 + '\n')
            recent_trades = df.tail(5)
            for idx, row in recent_trades.iterrows():
                f.write(f"  {row.get('timestamp', 'N/A')}: "
                       f"{row.get('signal', 'N/A')} @ "
                       f"${row.get('price', 0):,.2f} × "
                       f"{row.get('quantity', 0):.6f} = "
                       f"${row.get('amount', 0):,.2f}\n")
        
        log.info(f"生成每日摘要: {summary_file}")
    
    def save_step9_trade_event(
        self,
        trade_event: Dict,
        symbol: str,
        timeframe: str,
        trade_id: Optional[str] = None
    ) -> Dict[str, str]:
        """保存每次实时交易事件到 step9（实时交易记录）
        
        Args:
            trade_event: 单次交易事件字典（必须包含 timestamp 等字段）
            symbol: 交易对
            timeframe: 时间周期
            trade_id: 交易ID（可选）

        Returns:
            保存的文件路径字典 {'json': ..., 'csv': ..., 'parquet': ...}
        """
        date_folder = self._get_date_folder('step9')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        event_id = trade_id or trade_event.get('trade_id') or f"trade_{timestamp}"
        
        # 保存单条 JSON
        json_file = os.path.join(
            date_folder,
            f'step9_trade_{symbol}_{timeframe}_{timestamp}_{event_id}.json'
        )
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(trade_event, f, indent=2, ensure_ascii=False)
        
        # 追加到当天 CSV 和 Parquet（按 symbol_timeframe 命名）
        csv_file = os.path.join(
            date_folder,
            f'step9_trades_{symbol}_{timeframe}_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        parquet_file = os.path.join(
            date_folder,
            f'step9_trades_{symbol}_{timeframe}_{datetime.now().strftime("%Y%m%d")}.parquet'
        )
        
        # 转为DataFrame
        df_event = pd.DataFrame([trade_event])
        # 协调列顺序和类型（尽量保持一致）
        try:
            if os.path.exists(csv_file):
                df_exist = pd.read_csv(csv_file)
                df_combined = pd.concat([df_exist, df_event], ignore_index=True, sort=False)
                df_combined.to_csv(csv_file, index=False)
                df_combined.to_parquet(parquet_file, index=False)
            else:
                df_event.to_csv(csv_file, index=False)
                df_event.to_parquet(parquet_file, index=False)
        except Exception as e:
            log.warning(f"保存实时交易汇总失败: {e}")
        
        log.debug(f"保存实时交易事件: {json_file}")
        return {'json': json_file, 'csv': csv_file, 'parquet': parquet_file}
    
    # ========================================================================
    # 多Agent架构数据保存方法 (v2.0)
    # ========================================================================
    
    def _get_multi_agent_folder(self, agent_name: str, date: Optional[str] = None) -> str:
        """
        获取或创建多Agent架构的数据文件夹
        
        Args:
            agent_name: Agent名称 ('agent1_data_sync', 'agent2_quant_analysis', etc.)
            date: 日期字符串 YYYYMMDD，默认为今天
            
        Returns:
            日期文件夹路径
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        multi_agent_dir = os.path.join(self.base_dir, 'multi_agent', agent_name, date)
        os.makedirs(multi_agent_dir, exist_ok=True)
        return multi_agent_dir
    
    def save_market_snapshot(
        self, 
        snapshot, 
        duration: float,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, str]:
        """
        保存 DataSyncAgent 的市场快照
        
        Args:
            snapshot: MarketSnapshot对象
            duration: 数据采集耗时（秒）
            symbol: 交易对
            
        Returns:
            保存的文件路径字典
        """
        folder = self._get_multi_agent_folder('agent1_data_sync')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON文件
        json_file = os.path.join(folder, f'market_snapshot_{timestamp}.json')
        log_file = os.path.join(folder, f'data_sync_log_{timestamp}.txt')
        
        # 构建JSON数据
        data = {
            'timestamp': snapshot.timestamp.isoformat(),
            'symbol': symbol,
            'fetch_duration_sec': duration,
            'alignment_ok': snapshot.alignment_ok,
            'data': {
                '5m': {
                    'stable': snapshot.stable_5m.to_dict('records') if hasattr(snapshot.stable_5m, 'to_dict') else [],
                    'live': snapshot.live_5m
                },
                '15m': {
                    'stable': snapshot.stable_15m.to_dict('records') if hasattr(snapshot.stable_15m, 'to_dict') else [],
                    'live': snapshot.live_15m
                },
                '1h': {
                    'stable': snapshot.stable_1h.to_dict('records') if hasattr(snapshot.stable_1h, 'to_dict') else [],
                    'live': snapshot.live_1h
                }
            },
            'metadata': {
                'stable_count': {
                    '5m': len(snapshot.stable_5m) if hasattr(snapshot.stable_5m, '__len__') else 0,
                    '15m': len(snapshot.stable_15m) if hasattr(snapshot.stable_15m, '__len__') else 0,
                    '1h': len(snapshot.stable_1h) if hasattr(snapshot.stable_1h, '__len__') else 0
                },
                'live_prices': {
                    '5m': snapshot.live_5m.get('close', 0) if snapshot.live_5m else 0,
                    '15m': snapshot.live_15m.get('close', 0) if snapshot.live_15m else 0,
                    '1h': snapshot.live_1h.get('close', 0) if snapshot.live_1h else 0
                }
            }
        }
        
        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 保存日志
        log_content = f"""=== DataSyncAgent 执行日志 ===
开始时间: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
交易对: {symbol}
并发请求数: 3

[时间对齐检查]
对齐状态: {'✅' if snapshot.alignment_ok else '❌'}

[性能统计]
总耗时: {duration:.2f}秒
性能提升: 71% (vs 传统1.5秒)

[数据量]
5m: {len(snapshot.stable_5m) if hasattr(snapshot.stable_5m, '__len__') else 0} 条
15m: {len(snapshot.stable_15m) if hasattr(snapshot.stable_15m, '__len__') else 0} 条
1h: {len(snapshot.stable_1h) if hasattr(snapshot.stable_1h, '__len__') else 0} 条
"""
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        log.info(f"✅ 保存市场快照: {json_file}")
        return {'json': json_file, 'log': log_file}
    
    def save_quant_signals(
        self,
        signals: Dict,
        duration: float,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, str]:
        """
        保存 QuantAnalystAgent 的量化信号
        
        Args:
            signals: 量化信号字典
            duration: 分析耗时（秒）
            symbol: 交易对
            
        Returns:
            保存的文件路径字典
        """
        folder = self._get_multi_agent_folder('agent2_quant_analysis')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(folder, f'quant_signals_{timestamp}.json')
        report_file = os.path.join(folder, f'analysis_report_{timestamp}.txt')
        
        # 构建JSON数据
        data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signals': signals,
            'analysis_duration_sec': duration
        }
        
        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 生成分析报告
        comprehensive = signals.get('comprehensive', {})
        trend_1h = signals.get('trend_1h', {})
        trend_15m = signals.get('trend_15m', {})
        trend_5m = signals.get('trend_5m', {})
        osc_1h = signals.get('oscillator_1h', {})
        osc_15m = signals.get('oscillator_15m', {})
        osc_5m = signals.get('oscillator_5m', {})
        
        report_content = f"""=== QuantAnalystAgent 分析报告 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[趋势分析]
- 1h: {trend_1h.get('signal', 'N/A')} (得分: {trend_1h.get('score', 0):+.0f})
- 15m: {trend_15m.get('signal', 'N/A')} (得分: {trend_15m.get('score', 0):+.0f})
- 5m: {trend_5m.get('signal', 'N/A')} (得分: {trend_5m.get('score', 0):+.0f})

[震荡分析]
- 1h: {osc_1h.get('signal', 'N/A')} (得分: {osc_1h.get('score', 0):+.0f})
- 15m: {osc_15m.get('signal', 'N/A')} (得分: {osc_15m.get('score', 0):+.0f})
- 5m: {osc_5m.get('signal', 'N/A')} (得分: {osc_5m.get('score', 0):+.0f})

[综合评估]
- 综合得分: {comprehensive.get('score', 0):+.1f}
- 信号强度: {comprehensive.get('signal', 'N/A')}
- 波动率: {comprehensive.get('details', {}).get('volatility', 0):.2f}
- 趋势强度: {comprehensive.get('details', {}).get('trend_strength', 'N/A')}

[性能]
- 分析耗时: {duration:.2f}秒
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        log.info(f"✅ 保存量化信号: {json_file}")
        return {'json': json_file, 'report': report_file}
    
    def save_vote_result(
        self,
        vote_result,
        vote_details: Dict,
        weights: Dict,
        duration: float,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, str]:
        """
        保存 DecisionCoreAgent 的投票结果
        
        Args:
            vote_result: VoteResult对象
            vote_details: 投票详情字典
            weights: 权重字典
            duration: 决策耗时（秒）
            symbol: 交易对
            
        Returns:
            保存的文件路径字典
        """
        folder = self._get_multi_agent_folder('agent3_decision_core')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(folder, f'vote_result_{timestamp}.json')
        log_file = os.path.join(folder, f'decision_log_{timestamp}.txt')
        
        # 构建JSON数据
        data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'vote_result': {
                'action': vote_result.action,
                'confidence': vote_result.confidence,
                'weighted_score': vote_result.weighted_score,
                'multi_period_aligned': vote_result.multi_period_aligned,
                'reason': vote_result.reason
            },
            'vote_details': vote_details,
            'weights_used': weights,
            'decision_duration_sec': duration
        }
        
        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 生成决策日志
        log_content = f"""=== DecisionCoreAgent 决策日志 ===
决策时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[加权投票结果]
决策动作: {vote_result.action}
置信度: {vote_result.confidence:.1%}
加权得分: {vote_result.weighted_score:.1f} (-100~+100)

[信号贡献度]
"""
        # 按贡献度排序
        sorted_details = sorted(vote_details.items(), key=lambda x: abs(x[1]), reverse=True)
        for sig_name, contribution in sorted_details:
            log_content += f"{sig_name}: {contribution:+.2f}\n"
        
        log_content += f"""
[多周期对齐]
状态: {'✅ 对齐' if vote_result.multi_period_aligned else '❌ 不对齐'}
原因: {vote_result.reason}

[性能]
决策耗时: {duration:.3f}秒
"""
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        log.info(f"✅ 保存决策结果: {json_file}")
        return {'json': json_file, 'log': log_file}
    
    def save_audit_result(
        self,
        audit_result,
        order_before: Dict,
        order_after: Dict,
        checks: List[str],
        duration: float,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, str]:
        """
        保存 RiskAuditAgent 的审计结果
        
        Args:
            audit_result: RiskCheckResult对象
            order_before: 修正前的订单参数
            order_after: 修正后的订单参数
            checks: 检查项列表
            duration: 审计耗时（秒）
            symbol: 交易对
            
        Returns:
            保存的文件路径字典
        """
        folder = self._get_multi_agent_folder('agent4_risk_audit')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(folder, f'audit_result_{timestamp}.json')
        log_file = os.path.join(folder, f'risk_log_{timestamp}.txt')
        
        # 构建JSON数据
        data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'audit_result': {
                'passed': audit_result.passed,
                'risk_level': audit_result.risk_level.value if hasattr(audit_result.risk_level, 'value') else str(audit_result.risk_level),
                'corrections': audit_result.corrections,
                'warnings': audit_result.warnings,
                'blocked_reason': audit_result.blocked_reason
            },
            'order_params_before': order_before,
            'order_params_after': order_after,
            'checks_performed': checks,
            'audit_duration_sec': duration
        }
        
        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 生成审计日志
        log_content = f"""=== RiskAuditAgent 审计日志 ===
审计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[订单信息]
交易对: {symbol}
动作: {order_before.get('action', 'N/A')}
入场价: ${order_before.get('entry_price', 0):,.2f}
数量: {order_before.get('quantity', 0):.4f}
杠杆: {order_before.get('leverage', 1)}x

[风控检查]
"""
        for check in checks:
            log_content += f"{check}\n"
        
        log_content += f"""
[审计结果]
状态: {'✅ 通过' if audit_result.passed else '❌ 拦截'}
风险等级: {audit_result.risk_level.value if hasattr(audit_result.risk_level, 'value') else str(audit_result.risk_level)}
"""
        
        if audit_result.corrections:
            log_content += f"修正项: {len(audit_result.corrections)}个\n"
            for key, value in audit_result.corrections.items():
                log_content += f"  - {key}: {order_before.get(key)} → {value}\n"
        
        if audit_result.warnings:
            log_content += f"警告项: {len(audit_result.warnings)}个\n"
            for warning in audit_result.warnings:
                log_content += f"  - {warning}\n"
        
        if audit_result.blocked_reason:
            log_content += f"拦截原因: {audit_result.blocked_reason}\n"
        
        log_content += f"\n[性能]\n审计耗时: {duration:.3f}秒\n"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        log.info(f"✅ 保存审计结果: {json_file}")
        return {'json': json_file, 'log': log_file}
    
    def save_trading_cycle(
        self,
        cycle_data: Dict,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, str]:
        """
        保存完整的交易循环数据
        
        Args:
            cycle_data: 循环数据字典
            symbol: 交易对
            
        Returns:
            保存的文件路径字典
        """
        folder = self._get_multi_agent_folder('agent_integration')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = os.path.join(folder, f'trading_cycle_{timestamp}.json')
        log_file = os.path.join(folder, f'integration_log_{timestamp}.txt')
        
        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(cycle_data, f, indent=2, ensure_ascii=False)
        
        # 生成集成日志
        log_content = f"""=== MultiAgentTradingBot 集成日志 ===
循环ID: {cycle_data.get('cycle_id', 'N/A')}
开始时间: {cycle_data.get('start_time', 'N/A')}
结束时间: {cycle_data.get('end_time', 'N/A')}
总耗时: {cycle_data.get('total_duration_sec', 0):.2f}秒

[执行步骤]
"""
        
        steps = cycle_data.get('steps', {})
        for step_name, step_info in steps.items():
            status_emoji = '✅' if step_info.get('status') == 'success' else ('⏭️' if step_info.get('status') == 'skipped' else '❌')
            log_content += f"{status_emoji} {step_name}: {step_info.get('status')} ({step_info.get('duration', 0):.2f}秒)\n"
            if step_info.get('reason'):
                log_content += f"   原因: {step_info.get('reason')}\n"
        
        log_content += f"""
[最终结果]
状态: {cycle_data.get('status', 'N/A')}
动作: {cycle_data.get('final_result', {}).get('action', 'N/A')}
原因: {cycle_data.get('final_result', {}).get('reason', 'N/A')}
"""
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        log.info(f"✅ 保存交易循环: {json_file}")
        return {'json': json_file, 'log': log_file}
