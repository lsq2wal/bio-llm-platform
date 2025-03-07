import os
import sys

# 添加 backend 目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入 pipeline
from app.llm.pipeline import LLMAnalysisPipeline

# 测试代码
if __name__ == "__main__":
    pipeline = LLMAnalysisPipeline()
    print("Pipeline 初始化成功") 