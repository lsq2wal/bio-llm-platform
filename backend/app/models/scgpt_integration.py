"""
scGPT模型集成模块: 用于细胞类型注释和生物数据分析
"""

import os
import logging
import torch
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple

# 假设scGPT已经安装并可以导入
try:
    import scgpt
    from scgpt.model import AutoConfig, AutoModelForMaskedLM
    from scgpt.tokenizer import GeneVocab
    from scgpt.tokenizer.gene_tokenizer import TokenizerForSC
except ImportError:
    logging.warning("scGPT模块未安装，某些功能可能不可用")

class ScGPTModel:
    """scGPT模型封装类"""
    
    def __init__(self, model_path: str, device: str = None):
        """
        初始化scGPT模型
        
        Args:
            model_path: 模型路径
            device: 设备（'cuda'或'cpu'）
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.logger.info(f"初始化scGPT模型，设备: {self.device}")
        
        try:
            # 加载配置
            self.config = AutoConfig.from_pretrained(model_path)
            
            # 加载模型
            self.model = AutoModelForMaskedLM.from_pretrained(
                model_path,
                config=self.config
            )
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            
            # 加载词汇表和分词器
            vocab_file = os.path.join(model_path, "vocab.json")
            gene_vocab = GeneVocab.from_file(vocab_file)
            self.tokenizer = TokenizerForSC(gene_vocab)
            
            self.logger.info("scGPT模型加载成功")
        except Exception as e:
            self.logger.error(f"scGPT模型加载失败: {str(e)}")
            raise e
    
    def annotate_cell_types(self, gene_expr_matrix: pd.DataFrame, cell_type_markers: Dict[str, List[str]], 
                           confidence_threshold: float = 0.7) -> Tuple[np.ndarray, np.ndarray]:
        """
        对单细胞数据进行细胞类型注释
        
        Args:
            gene_expr_matrix: 基因表达矩阵 (cells x genes)
            cell_type_markers: 细胞类型marker基因字典
            confidence_threshold: 置信度阈值
            
        Returns:
            预测的细胞类型和置信度
        """
        try:
            self.logger.info("开始细胞类型注释")
            
            # 将DataFrame转换为模型输入
            input_ids_list = []
            attention_mask_list = []
            
            for idx, cell_vec in gene_expr_matrix.iterrows():
                # 选择高表达基因作为输入
                expr_genes = cell_vec[cell_vec > 0].index.tolist()
                
                # 标记化处理
                tokenized = self.tokenizer(
                    expr_genes,
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
                
                input_ids_list.append(tokenized["input_ids"])
                attention_mask_list.append(tokenized["attention_mask"])
            
            # 批量处理
            all_input_ids = torch.cat(input_ids_list, dim=0).to(self.device)
            all_attention_mask = torch.cat(attention_mask_list, dim=0).to(self.device)
            
            # 批量推理
            cell_type_probs = []
            cell_types = list(cell_type_markers.keys())
            
            with torch.no_grad():
                batch_size = 32
                for i in range(0, len(all_input_ids), batch_size):
                    batch_input_ids = all_input_ids[i:i+batch_size]
                    batch_attention_mask = all_attention_mask[i:i+batch_size]
                    
                    # 获取模型输出向量
                    outputs = self.model(
                        input_ids=batch_input_ids,
                        attention_mask=batch_attention_mask,
                        output_hidden_states=True
                    )
                    
                    # 使用[CLS]令牌的输出表示每个细胞
                    cell_embeddings = outputs.hidden_states[-1][:, 0, :]
                    
                    # 计算与每个细胞类型的相似度
                    batch_probs = []
                    for cell_type, markers in cell_type_markers.items():
                        # 将marker基因转换为嵌入向量
                        marker_tokens = [self.tokenizer.convert_tokens_to_ids(marker) for marker in markers if marker in self.tokenizer.vocab]
                        
                        if len(marker_tokens) == 0:
                            # 如果没有找到marker基因，则跳过
                            batch_probs.append(torch.zeros(len(batch_input_ids), 1).to(self.device))
                            continue
                            
                        # 查询模型的嵌入层
                        marker_embeddings = self.model.get_input_embeddings()(torch.tensor(marker_tokens).to(self.device))
                        
                        # 计算平均marker嵌入
                        marker_centroid = marker_embeddings.mean(dim=0).unsqueeze(0)
                        
                        # 计算余弦相似度
                        similarity = torch.nn.functional.cosine_similarity(
                            cell_embeddings, 
                            marker_centroid.expand(cell_embeddings.size(0), -1),
                            dim=1
                        )
                        
                        batch_probs.append(similarity.unsqueeze(1))
                    
                    # 连接所有细胞类型的概率
                    batch_cell_type_probs = torch.cat(batch_probs, dim=1)
                    cell_type_probs.append(batch_cell_type_probs.cpu().numpy())
            
            # 合并所有批次的结果
            all_probs = np.concatenate(cell_type_probs, axis=0)
            
            # Softmax归一化获得概率
            exp_probs = np.exp(all_probs)
            norm_probs = exp_probs / np.sum(exp_probs, axis=1, keepdims=True)
            
            # 获取最可能的细胞类型和置信度
            predicted_indices = np.argmax(norm_probs, axis=1)
            predicted_probs = np.max(norm_probs, axis=1)
            
            # 转换为细胞类型名称
            predicted_cell_types = np.array([cell_types[i] if predicted_probs[idx] >= confidence_threshold else "Unknown" 
                                            for idx, i in enumerate(predicted_indices)])
            
            self.logger.info(f"细胞类型注释完成, 标注了 {len(predicted_cell_types)} 个细胞")
            return predicted_cell_types, predicted_probs
        
        except Exception as e:
            self.logger.error(f"细胞类型注释失败: {str(e)}")
            raise e
    
    def analyze_gene_perturbation(self, gene_expr_matrix: pd.DataFrame, target_genes: List[str],
                                 n_top_responses: int = 100) -> Dict[str, Any]:
        """
        分析基因扰动效应
        
        Args:
            gene_expr_matrix: 基因表达矩阵
            target_genes: 目标扰动基因列表
            n_top_responses: 返回的顶部响应基因数量
            
        Returns:
            扰动分析结果字典
        """
        try:
            self.logger.info(f"开始基因扰动分析，目标基因: {target_genes}")
            
            # 将目标基因转换为模型词汇表ID
            target_ids = []
            for gene in target_genes:
                if gene in self.tokenizer.vocab:
                    target_ids.append(self.tokenizer.convert_tokens_to_ids(gene))
                else:
                    self.logger.warning(f"基因 {gene} 不在词汇表中，将被忽略")
            
            if not target_ids:
                raise ValueError("所有目标基因都不在模型词汇表中")
            
            # 为每个细胞准备输入
            results = {}
            
            # 准备待掩码的目标基因输入
            with torch.no_grad():
                # 对每个目标基因进行分析
                for target_gene, target_id in zip(target_genes, target_ids):
                    self.logger.info(f"分析基因 {target_gene} 的扰动效应")
                    
                    # 获取所有基因的响应分数
                    all_gene_scores = []
                    
                    for idx, cell_vec in gene_expr_matrix.iterrows():
                        # 选择高表达基因作为输入
                        expr_genes = cell_vec[cell_vec > 0].index.tolist()
                        
                        # 如果目标基因不在表达基因中，则添加它
                        if target_gene not in expr_genes:
                            expr_genes.append(target_gene)
                        
                        # 标记化处理
                        tokenized = self.tokenizer(
                            expr_genes,
                            padding="max_length",
                            truncation=True,
                            max_length=512,
                            return_tensors="pt"
                        )
                        
                        # 找到目标基因的位置
                        target_positions = (tokenized["input_ids"] == target_id).nonzero(as_tuple=True)[1]
                        
                        if len(target_positions) == 0:
                            continue
                            
                        # 创建mask输入
                        masked_input_ids = tokenized["input_ids"].clone()
                        masked_input_ids[0, target_positions[0]] = self.tokenizer.mask_token_id
                        
                        # 运行模型进行预测
                        outputs = self.model(
                            input_ids=masked_input_ids.to(self.device),
                            attention_mask=tokenized["attention_mask"].to(self.device)
                        )
                        
                        # 获取掩码位置的预测
                        mask_pos = target_positions[0]
                        logits = outputs.logits[0, mask_pos, :]
                        probs = torch.softmax(logits, dim=0).cpu().numpy()
                        
                        # 保存所有基因的概率分数
                        all_gene_scores.append(probs)
                    
                    if not all_gene_scores:
                        self.logger.warning(f"没有找到基因 {target_gene} 的扰动效应数据")
                        continue
                        
                    # 计算平均分数
                    avg_scores = np.mean(all_gene_scores, axis=0)
                    
                    # 获取前N个响应基因
                    top_indices = np.argsort(-avg_scores)[:n_top_responses]
                    top_genes = [self.tokenizer.convert_ids_to_tokens(idx) for idx in top_indices 
                                if self.tokenizer.convert_ids_to_tokens(idx) != target_gene]
                    top_scores = [float(avg_scores[idx]) for idx in top_indices]
                    
                    # 组装结果
                    results[target_gene] = {
                        "top_response_genes": top_genes[:n_top_responses],
                        "response_scores": top_scores[:n_top_responses],
                    }
            
            self.logger.info("基因扰动分析完成")
            return results
        
        except Exception as e:
            self.logger.error(f"基因扰动分析失败: {str(e)}")
            raise e 