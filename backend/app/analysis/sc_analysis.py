import scanpy as sc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional, Tuple
import logging
import os

class SingleCellAnalysis:
    """单细胞分析核心类"""
    
    def __init__(self, data_path: str, output_path: str):
        self.logger = logging.getLogger(__name__)
        self.data_path = data_path
        self.output_path = output_path
        self.adata = None
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
    
    def load_data(self) -> bool:
        """加载单细胞数据"""
        try:
            self.logger.info(f"加载数据: {self.data_path}")
            
            if self.data_path.endswith('.h5ad'):
                self.adata = sc.read_h5ad(self.data_path)
            elif self.data_path.endswith('.mtx'):
                # 读取10x格式
                self.adata = sc.read_10x_mtx(
                    os.path.dirname(self.data_path),
                    var_names='gene_symbols',
                    cache=True
                )
            elif self.data_path.endswith('.csv'):
                self.adata = sc.read_csv(self.data_path)
            else:
                self.logger.error(f"不支持的文件格式: {self.data_path}")
                return False
            
            self.logger.info(f"数据加载成功，形状: {self.adata.shape}")
            return True
        except Exception as e:
            self.logger.error(f"加载数据失败: {str(e)}")
            return False
    
    def preprocess(self, min_genes: int = 200, min_cells: int = 3, 
                  max_genes: int = 5000, max_mt_percent: float = 10.0) -> bool:
        """预处理数据"""
        try:
            # 质量控制
            sc.pp.calculate_qc_metrics(self.adata, qc_vars=['mt'], inplace=True)
            
            # 过滤细胞和基因
            self.adata = self.adata[self.adata.obs.n_genes_by_counts > min_genes, :]
            self.adata = self.adata[self.adata.obs.n_genes_by_counts < max_genes, :]
            self.adata = self.adata[self.adata.obs.pct_counts_mt < max_mt_percent, :]
            
            # 过滤低表达基因
            sc.pp.filter_genes(self.adata, min_cells=min_cells)
            
            # 标准预处理流程
            sc.pp.normalize_total(self.adata, target_sum=1e4)
            sc.pp.log1p(self.adata)
            sc.pp.highly_variable_genes(self.adata, n_top_genes=2000)
            
            # 保存预处理后的数据
            self.adata.write(os.path.join(self.output_path, 'preprocessed.h5ad'))
            
            return True
        except Exception as e:
            self.logger.error(f"预处理失败: {str(e)}")
            return False
    
    def batch_correction(self, batch_key: str, method: str = 'harmony') -> bool:
        """批次效应校正"""
        try:
            if method == 'harmony':
                # 先进行PCA
                sc.pp.pca(self.adata)
                # 然后使用Harmony
                import harmonypy
                from harmonypy import run_harmony
                
                harmony_out = run_harmony(
                    self.adata.obsm['X_pca'], 
                    self.adata.obs, 
                    batch_key
                )
                self.adata.obsm['X_harmony'] = harmony_out.Z_corr
                # 使用harmony校正后的矩阵进行后续分析
                self.adata.uns['X_emb'] = 'X_harmony'
                
                # 使用harmony校正后的结果进行降维
                sc.pp.neighbors(self.adata, use_rep='X_harmony')
                sc.tl.umap(self.adata)
                
            elif method == 'bbknn':
                # 使用BBKNN进行批次校正
                import bbknn
                # 先进行PCA
                sc.pp.pca(self.adata)
                # 直接用BBKNN构建批次校正后的KNN图
                bbknn.bbknn(self.adata, batch_key=batch_key)
                sc.tl.umap(self.adata)
                
            elif method == 'scanorama':
                # 使用Scanorama进行批次校正
                import scanorama
                
                # 需要按批次拆分数据
                batches = self.adata.obs[batch_key].cat.categories
                adatas = {}
                for batch in batches:
                    adatas[batch] = self.adata[self.adata.obs[batch_key] == batch].copy()
                
                # 准备数据
                datasets_dimred, datasets_corrected = scanorama.correct_scanpy(
                    [adatas[batch] for batch in batches],
                    return_dimred=True
                )
                
                # 把校正后的结果放回原数据
                self.adata.obsm['X_scanorama'] = np.zeros((self.adata.shape[0], datasets_dimred[0].shape[1]))
                
                start = 0
                for i, batch in enumerate(batches):
                    n_cells = adatas[batch].shape[0]
                    self.adata.obsm['X_scanorama'][start:start+n_cells] = datasets_dimred[i]
                    start += n_cells
                
                # 使用scanorama校正后的结果进行降维
                sc.pp.neighbors(self.adata, use_rep='X_scanorama')
                sc.tl.umap(self.adata)
            
            else:
                self.logger.error(f"不支持的批次校正方法: {method}")
                return False
            
            # 保存批次校正后的数据
            self.adata.write(os.path.join(self.output_path, 'batch_corrected.h5ad'))
            
            return True
        except Exception as e:
            self.logger.error(f"批次校正失败: {str(e)}")
            return False
    
    def clustering(self, resolution: float = 0.5) -> bool:
        """聚类分析"""
        try:
            # 执行聚类
            sc.tl.leiden(self.adata, resolution=resolution)
            
            # 计算每个簇的marker基因
            sc.tl.rank_genes_groups(self.adata, 'leiden', method='wilcoxon')
            
            # 保存聚类结果
            self.adata.write(os.path.join(self.output_path, 'clustered.h5ad'))
            
            return True
        except Exception as e:
            self.logger.error(f"聚类失败: {str(e)}")
            return False
    
    def cell_type_annotation(self, method: str = 'scgpt', model_path: str = None) -> bool:
        """细胞类型注释"""
        try:
            if method == 'scgpt':
                # 使用scGPT进行细胞类型注释
                from app.models.scgpt.inference import SCGPTAnnotator
                
                annotator = SCGPTAnnotator(model_path=model_path)
                cell_types = annotator.predict(self.adata)
                
                # 将注释结果添加到adata
                self.adata.obs['predicted_cell_type'] = cell_types
                
            elif method == 'marker_genes':
                # 基于已知marker基因进行注释
                marker_dict = {
                    'T细胞': ['CD3D', 'CD3E', 'CD3G', 'CD8A', 'CD4'],
                    'B细胞': ['CD19', 'CD79A', 'CD79B', 'MS4A1'],
                    'NK细胞': ['NCAM1', 'NKG7', 'KLRD1'],
                    '单核细胞': ['CD14', 'LYZ', 'CSF1R'],
                    '巨噬细胞': ['CD68', 'CD163', 'MRC1'],
                    '树突状细胞': ['ITGAX', 'CLEC9A', 'CD1C'],
                    '上皮细胞': ['EPCAM', 'KRT8', 'KRT18'],
                    '成纤维细胞': ['COL1A1', 'DCN', 'LUM']
                }
                
                # 为每个细胞计算每个细胞类型的得分
                cell_type_scores = {}
                for cell_type, markers in marker_dict.items():
                    # 获取存在于数据中的marker
                    existing_markers = [m for m in markers if m in self.adata.var_names]
                    if not existing_markers:
                        continue
                    
                    # 计算marker基因的平均表达
                    cell_type_scores[cell_type] = self.adata[:, existing_markers].X.mean(axis=1)
                
                # 转换为DataFrame
                scores_df = pd.DataFrame(cell_type_scores, index=self.adata.obs_names)
                
                # 分配细胞类型（选择得分最高的类型）
                predicted_types = scores_df.idxmax(axis=1)
                self.adata.obs['predicted_cell_type'] = predicted_types
                
            else:
                self.logger.error(f"不支持的注释方法: {method}")
                return False
            
            # 保存注释结果
            self.adata.write(os.path.join(self.output_path, 'annotated.h5ad'))
            
            return True
        except Exception as e:
            self.logger.error(f"细胞类型注释失败: {str(e)}")
            return False
    
    def generate_plots(self) -> bool:
        """生成可视化图表"""
        try:
            # 创建图表目录
            plots_dir = os.path.join(self.output_path, 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            # QC指标可视化
            sc.pl.violin(self.adata, ['n_genes_by_counts', 'total_counts', 'pct_counts_mt'],
                        jitter=0.4, multi_panel=True,
                        save=os.path.join(plots_dir, 'qc_metrics.pdf'))
            
            # UMAP聚类可视化
            sc.pl.umap(self.adata, color=['leiden'], 
                      save=os.path.join(plots_dir, 'umap_clusters.pdf'))
            
            # 如果有细胞类型注释，则可视化
            if 'predicted_cell_type' in self.adata.obs:
                sc.pl.umap(self.adata, color=['predicted_cell_type'], 
                          save=os.path.join(plots_dir, 'umap_cell_types.pdf'))
            
            # 热图展示各簇marker基因
            sc.pl.rank_genes_groups_heatmap(self.adata, n_genes=10, 
                                          save=os.path.join(plots_dir, 'marker_genes_heatmap.pdf'))
            
            # 气泡图展示各簇特征基因
            sc.pl.rank_genes_groups_dotplot(self.adata, n_genes=5, 
                                          save=os.path.join(plots_dir, 'marker_genes_dotplot.pdf'))
            
            # 保存数据用于前端可视化
            self._export_for_plotly()
            
            return True
        except Exception as e:
            self.logger.error(f"生成可视化图表失败: {str(e)}")
            return False
    
    def _export_for_plotly(self):
        """导出数据用于前端Plotly.js可视化"""
        try:
            # 导出UMAP坐标和元数据
            umap_coords = self.adata.obsm['X_umap']
            
            # 准备数据
            export_data = {
                'umap': {
                    'x': umap_coords[:, 0].tolist(),
                    'y': umap_coords[:, 1].tolist()
                },
                'metadata': {}
            }
            
            # 添加聚类信息
            if 'leiden' in self.adata.obs:
                export_data['metadata']['cluster'] = self.adata.obs['leiden'].astype(str).tolist()
            
            # 添加细胞类型注释（如果有）
            if 'predicted_cell_type' in self.adata.obs:
                export_data['metadata']['cell_type'] = self.adata.obs['predicted_cell_type'].astype(str).tolist()
            
            # 添加QC指标
            for metric in ['n_genes_by_counts', 'total_counts', 'pct_counts_mt']:
                if metric in self.adata.obs:
                    export_data['metadata'][metric] = self.adata.obs[metric].tolist()
            
            # 保存为JSON文件
            import json
            json_path = os.path.join(self.output_path, 'plotly_data.json')
            with open(json_path, 'w') as f:
                json.dump(export_data, f)
                
            # 导出热门基因的表达数据
            n_top_genes = 50
            if hasattr(self.adata, 'uns') and 'rank_genes_groups' in self.adata.uns:
                top_genes = []
                for i in range(min(n_top_genes, self.adata.uns['rank_genes_groups']['names'].shape[1])):
                    for cluster in self.adata.uns['rank_genes_groups']['names'].dtype.names:
                        gene = self.adata.uns['rank_genes_groups']['names'][cluster][i]
                        if gene not in top_genes:
                            top_genes.append(gene)
                
                # 导出这些基因的表达数据
                gene_exp_data = {}
                for gene in top_genes:
                    if gene in self.adata.var_names:
                        gene_exp_data[gene] = self.adata[:, gene].X.toarray().flatten().tolist()
                
                # 保存为JSON
                gene_exp_path = os.path.join(self.output_path, 'gene_expression.json')
                with open(gene_exp_path, 'w') as f:
                    json.dump(gene_exp_data, f)
                    
        except Exception as e:
            self.logger.error(f"导出前端可视化数据失败: {str(e)}")
    
    def generate_report(self) -> bool:
        """生成分析报告"""
        try:
            # 使用nbconvert基于模板生成HTML报告
            import nbformat as nbf
            from nbconvert import HTMLExporter
            import datetime
            
            # 创建一个notebook对象
            nb = nbf.v4.new_notebook()
            
            # 添加标题单元格
            title_cell = nbf.v4.new_markdown_cell(f"""
            # 单细胞RNA-seq分析报告
            **分析时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            **数据路径:** {self.data_path}
            **输出路径:** {self.output_path}
            """)
            
            # 添加数据描述单元格
            data_cell = nbf.v4.new_markdown_cell(f"""
            ## 数据描述
            
            - 细胞数量: {self.adata.n_obs}
            - 基因数量: {self.adata.n_vars}
            - 批次数量: {self.adata.obs['batch'].nunique() if 'batch' in self.adata.obs else 'N/A'}
            """)
            
            # 添加预处理描述
            preprocess_cell = nbf.v4.new_markdown_cell("""
            ## 预处理步骤
            
            1. 细胞质量控制（过滤低质量细胞）
            2. 基因过滤（移除低表达基因）
            3. 数据标准化
            4. 特征选择（高变异基因）
            5. 批次效应校正（如果适用）
            """)
            
            # 添加图像单元格（嵌入图像文件）
            plots_dir = os.path.join(self.output_path, 'plots')
            plots_cell = nbf.v4.new_markdown_cell("""
            ## 可视化结果
            
            ### 聚类分析
            ![UMAP聚类结果](plots/umap_clusters.pdf)
            
            ### 细胞类型注释
            ![细胞类型注释](plots/umap_cell_types.pdf)
            
            ### Marker基因热图
            ![Marker基因热图](plots/marker_genes_heatmap.pdf)
            
            ### Marker基因气泡图
            ![Marker基因气泡图](plots/marker_genes_dotplot.pdf)
            """)
            
            # 添加结论单元格
            if 'predicted_cell_type' in self.adata.obs:
                # 计算每种细胞类型的数量
                cell_type_counts = self.adata.obs['predicted_cell_type'].value_counts()
                cell_type_percentages = cell_type_counts / cell_type_counts.sum() * 100
                
                cell_type_table = "| 细胞类型 | 数量 | 百分比 |\n|----------|------|---------|\n"
                for cell_type, count in cell_type_counts.items():
                    percentage = cell_type_percentages[cell_type]
                    cell_type_table += f"| {cell_type} | {count} | {percentage:.2f}% |\n"
                
                conclusion_cell = nbf.v4.new_markdown_cell(f"""
                ## 结论
                
                ### 细胞类型组成
                
                {cell_type_table}
                
                ### 主要发现
                
                - 数据中识别出{len(cell_type_counts)}种主要细胞类型
                - 主要细胞类型是{cell_type_counts.index[0]}，占比{cell_type_percentages.iloc[0]:.2f}%
                """)
            else:
                conclusion_cell = nbf.v4.new_markdown_cell("""
                ## 结论
                
                - 聚类分析完成，请查看UMAP可视化结果
                - 尚未进行细胞类型注释
                """)
            
            # 添加所有单元格到notebook
            nb.cells.extend([title_cell, data_cell, preprocess_cell, plots_cell, conclusion_cell])
            
            # 转换为HTML
            html_exporter = HTMLExporter()
            html_exporter.template_name = 'classic'
            (body, resources) = html_exporter.from_notebook_node(nb)
            
            # 保存HTML报告
            report_path = os.path.join(self.output_path, 'analysis_report.html')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(body)
            
            return True
        except Exception as e:
            self.logger.error(f"生成报告失败: {str(e)}")
            return False 