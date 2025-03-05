#!/bin/bash
#
# 多瑙调度器提交脚本：单细胞分析任务
#
#DONAU -N sc_analysis_${TASK_ID}
#DONAU -n 1
#DONAU -c 24
#DONAU --gpus 1
#DONAU -p gpu
#DONAU -t 12:00:00
#DONAU --constraint="A100"
#DONAU -o logs/sc_analysis_${TASK_ID}.out
#DONAU -e logs/sc_analysis_${TASK_ID}.err

# 加载环境模块
module load anaconda/2021.11
module load cuda/11.7

# 激活conda环境
source activate bio-llm-env

# 设置环境变量
export PYTHONPATH=/path/to/project:$PYTHONPATH
export HF_HOME=/path/to/huggingface/cache
export TRANSFORMERS_CACHE=/path/to/transformers/cache

# 执行分析脚本
python /path/to/project/backend/app/analysis/run_analysis.py \
    --task_id ${TASK_ID} \
    --data_path ${DATA_PATH} \
    --output_path ${OUTPUT_PATH} \
    --config ${CONFIG_PATH}

# 检查运行状态
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "分析脚本运行失败，退出代码: $exit_code"
    exit $exit_code
fi

# 复制结果到共享存储
mkdir -p /shared/results/${USER}/${TASK_ID}
cp -r ${OUTPUT_PATH}/* /shared/results/${USER}/${TASK_ID}/

echo "分析任务完成，结果已保存到: /shared/results/${USER}/${TASK_ID}/" 