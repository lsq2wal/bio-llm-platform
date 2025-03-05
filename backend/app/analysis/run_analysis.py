#!/usr/bin/env python3
"""
分析执行脚本: 用于HPC环境下执行分析任务
"""

import argparse
import json
import logging
import os
import sys
import traceback
from typing import Dict, Any
import time

from app.analysis.sc_analysis import SingleCellAnalysis
from app.core.config import settings

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analysis.log')
    ]
)
logger = logging.getLogger("analysis")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='执行生物数据分析任务')
    parser.add_argument('--task_id', type=str, required=True, help='任务ID')
    parser.add_argument('--data_path', type=str, required=True, help='数据路径')
    parser.add_argument('--output_path', type=str, required=True, help='输出路径')
    parser.add_argument('--config', type=str, required=True, help='分析配置文件路径')
    return parser.parse_args()

def update_progress(task_id: str, progress: float, status: str, error: str = None):
    """更新任务进度（简化版本）"""
    progress_file = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/progress/{task_id}.json"
    os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    
    progress_data = {
        "task_id": task_id,
        "progress": progress,
        "status": status,
        "timestamp": time.time(),
        "error": error
    }
    
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)
    
    logger.info(f"任务 {task_id} 进度更新: {progress:.2f}, 状态: {status}")

def run_analysis(task_id: str, data_path: str, output_path: str, config: Dict[str, Any]):
    """运行分析流程"""
    try:
        # 更新初始进度
        update_progress(task_id, 0.0, "running")
        
        # 确定分析类型
        analysis_type = config.get("analysis_type", "single_cell")
        
        if analysis_type == "single_cell":
            # 创建单细胞分析实例
            analyzer = SingleCellAnalysis(data_path, output_path)
            
            # 加载数据
            logger.info("开始加载数据...")
            if not analyzer.load_data():
                raise Exception("加载数据失败")
            update_progress(task_id, 0.1, "running")
            
            # 预处理数据
            logger.info("开始预处理数据...")
            preprocess_params = config.get("preprocess_params", {})
            if not analyzer.preprocess(**preprocess_params):
                raise Exception("预处理数据失败")
            update_progress(task_id, 0.3, "running")
            
            # 批次效应校正（如果需要）
            if "batch_correction" in config and config["batch_correction"]["enabled"]:
                logger.info("开始批次效应校正...")
                bc_params = config["batch_correction"]
                if not analyzer.batch_correction(
                    batch_key=bc_params.get("batch_key", "batch"),
                    method=bc_params.get("method", "harmony")
                ):
                    raise Exception("批次效应校正失败")
            update_progress(task_id, 0.5, "running")
            
            # 聚类分析
            logger.info("开始聚类分析...")
            clustering_params = config.get("clustering_params", {})
            if not analyzer.clustering(**clustering_params):
                raise Exception("聚类分析失败")
            update_progress(task_id, 0.7, "running")
            
            # 细胞类型注释（如果需要）
            if "cell_annotation" in config and config["cell_annotation"]["enabled"]:
                logger.info("开始细胞类型注释...")
                annotation_params = config["cell_annotation"]
                if not analyzer.cell_type_annotation(
                    method=annotation_params.get("method", "scgpt"),
                    model_path=annotation_params.get("model_path", settings.SCGPT_MODEL_PATH)
                ):
                    raise Exception("细胞类型注释失败")
            update_progress(task_id, 0.8, "running")
            
            # 生成图表
            logger.info("生成可视化图表...")
            if not analyzer.generate_plots():
                raise Exception("生成可视化图表失败")
            update_progress(task_id, 0.9, "running")
            
            # 生成报告
            logger.info("生成分析报告...")
            if not analyzer.generate_report():
                raise Exception("生成分析报告失败")
            
            # 完成分析
            update_progress(task_id, 1.0, "completed")
            logger.info(f"分析任务 {task_id} 已完成")
            
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
        
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        logger.error(traceback.format_exc())
        update_progress(task_id, 0.0, "failed", str(e))
        sys.exit(1)

def main():
    """主函数"""
    args = parse_args()
    
    # 加载配置
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # 运行分析
    run_analysis(args.task_id, args.data_path, args.output_path, config)

if __name__ == "__main__":
    main() 