"""
RAG向量检索系统: 用于生物知识检索和LLM增强
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
import numpy as np

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import BaseRetriever

class BioKnowledgeRetriever(BaseRetriever):
    """生物知识检索器"""
    
    def __init__(
        self, 
        vector_store_path: str, 
        embedding_model: str = "all-MiniLM-L6-v2",
        top_k: int = 5
    ):
        """
        初始化生物知识检索器
        
        Args:
            vector_store_path: 向量存储路径
            embedding_model: 嵌入模型名称
            top_k: 检索的顶部文档数
        """
        self.logger = logging.getLogger(__name__)
        self.vector_store_path = vector_store_path
        self.top_k = top_k
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model
        )
        
        # 初始化向量存储
        self.init_vector_store()
    
    def init_vector_store(self) -> None:
        """初始化向量存储"""
        try:
            if os.path.exists(self.vector_store_path):
                self.logger.info(f"加载已有向量存储: {self.vector_store_path}")
                self.vector_store = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory=self.vector_store_path
                )
            else:
                self.logger.info(f"创建新的向量存储: {self.vector_store_path}")
                os.makedirs(self.vector_store_path, exist_ok=True)
                self.vector_store = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory=self.vector_store_path
                )
        except Exception as e:
            self.logger.error(f"初始化向量存储失败: {str(e)}")
            raise e
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
        """
        try:
            self.logger.info(f"添加 {len(documents)} 个文档到向量存储")
            
            # 文本分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            
            splits = text_splitter.split_documents(documents)
            self.logger.info(f"文档分割为 {len(splits)} 个片段")
            
            # 添加到向量存储
            self.vector_store.add_documents(splits)
            
            # 持久化
            self.vector_store.persist()
            self.logger.info("文档已添加并持久化")
        except Exception as e:
            self.logger.error(f"添加文档失败: {str(e)}")
            raise e
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            run_manager: 回调管理器
            
        Returns:
            相关文档列表
        """
        try:
            self.logger.info(f"检索查询: {query}")
            
            # 使用相似度搜索
            documents = self.vector_store.similarity_search(
                query=query,
                k=self.top_k
            )
            
            self.logger.info(f"检索到 {len(documents)} 个相关文档")
            return documents
        except Exception as e:
            self.logger.error(f"检索文档失败: {str(e)}")
            raise e

class BiologicalRAG:
    """生物学RAG系统"""
    
    def __init__(
        self,
        vector_store_path: str,
        llm_model_path: str,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        初始化生物学RAG系统
        
        Args:
            vector_store_path: 向量存储路径
            llm_model_path: LLM模型路径
            embedding_model: 嵌入模型名称
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化知识检索器
        self.retriever = BioKnowledgeRetriever(
            vector_store_path=vector_store_path,
            embedding_model=embedding_model
        )
        
        # 初始化LLM (需要根据实际部署环境调整)
        self.llm_model_path = llm_model_path
        
        try:
            from langchain.llms import HuggingFacePipeline
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            self.logger.info(f"加载LLM模型: {llm_model_path}")
            
            # 加载模型和分词器
            self.tokenizer = AutoTokenizer.from_pretrained(llm_model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                llm_model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True  # 对于大模型使用量化
            )
            
            # 创建pipeline
            pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            # 创建LangChain LLM
            self.llm = HuggingFacePipeline(pipeline=pipe)
            
            self.logger.info("LLM模型加载成功")
        except Exception as e:
            self.logger.error(f"LLM模型加载失败: {str(e)}")
            # 继续初始化其他部分，但LLM功能将不可用
            self.llm = None
    
    def get_rag_response(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        获取RAG增强的回答
        
        Args:
            query: 用户查询
            context: 额外上下文信息
            
        Returns:
            RAG响应结果
        """
        try:
            self.logger.info(f"处理RAG查询: {query}")
            
            if not self.llm:
                return {
                    "error": "LLM模型未成功加载，无法生成回答",
                    "retrieved_documents": []
                }
            
            # 检索相关文档
            documents = self.retriever.get_relevant_documents(query)
            
            # 提取文档内容
            retrieved_texts = []
            for i, doc in enumerate(documents):
                retrieved_texts.append(f"[{i+1}] {doc.page_content}")
            
            context_text = "\n\n".join(retrieved_texts)
            
            # 构建提示
            prompt = f"""
            你是一个专业的生物学家和生物信息学专家，请根据以下参考资料回答问题。
            
            参考资料:
            {context_text}
            
            用户额外提供的上下文：
            {context}
            
            问题: {query}
            
            请给出详细的解答，注明你使用的参考资料编号。如果参考资料中没有足够的信息，可以使用你的专业知识进行补充，但请明确指出哪些是来自参考资料的内容，哪些是你的专业知识补充。
            """
            
            # 生成回答
            response = self.llm.predict(prompt)
            
            return {
                "response": response,
                "retrieved_documents": [doc.page_content for doc in documents],
                "sources": [doc.metadata.get("source", "Unknown") for doc in documents]
            }
        
        except Exception as e:
            self.logger.error(f"生成RAG回答失败: {str(e)}")
            return {
                "error": str(e),
                "retrieved_documents": []
            } 