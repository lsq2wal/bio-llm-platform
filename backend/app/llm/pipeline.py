import os
from typing import Dict, Any, List
import logging
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings

class LLMAnalysisPipeline:
    """大模型驱动的分析流水线"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化LLM
        try:
            self.logger.info("初始化LLM模型...")
            self.llm = self._init_llm_model()
            
            # 初始化向量存储
            self.logger.info("初始化向量数据库连接...")
            self.vector_store = self._init_vector_store()
            
            # 初始化提示模板
            self.analysis_prompt = PromptTemplate(
                input_variables=["task_type", "description", "parameters", "context"],
                template="""
                你是一个生物数据分析专家，擅长处理基因组学和单细胞数据。
                
                任务类型: {task_type}
                用户描述: {description}
                参数配置: {parameters}
                
                相关知识背景:
                {context}
                
                请提供详细的分析计划，包括:
                1. 数据预处理步骤
                2. 分析方法与参数
                3. 可视化建议
                4. 解释与阐述重点
                
                以JSON格式输出你的分析计划:
                """
            )
            
            # 初始化分析链
            self.analysis_chain = LLMChain(
                llm=self.llm,
                prompt=self.analysis_prompt
            )
            
            self.logger.info("LLM分析流水线初始化完成")
        except Exception as e:
            self.logger.error(f"初始化LLM流水线失败: {str(e)}")
            raise e
    
    def _init_llm_model(self):
        """初始化LLM模型"""
        # 这里应该是实际从本地或远程加载LLM
        # 简化版本使用HuggingFacePipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        
        model_path = settings.LLM_MODEL_PATH
        self.logger.info(f"加载LLM模型: {model_path}")
        
        # 这里假设我们有一个已经下载好的Llama 3模型
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            device_map="auto",
            load_in_8bit=True  # 8-bit量化以减少内存消耗
        )
        
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1000,
            temperature=0.3,
            top_p=0.95,
            repetition_penalty=1.1
        )
        
        return HuggingFacePipeline(pipeline=pipe)
    
    def _init_vector_store(self):
        """初始化向量存储"""
        # 使用HuggingFace的嵌入模型
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # 连接到已存在的ChromaDB
        try:
            vector_store = Chroma(
                collection_name="bio_literature",
                embedding_function=embeddings,
                persist_directory="./chroma_db"
            )
            return vector_store
        except Exception as e:
            self.logger.error(f"连接ChromaDB失败: {str(e)}")
            # 如果连接失败，返回None，后续会处理这种情况
            return None
    
    async def parse_request(self, task_type: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析用户的分析请求，生成分析计划
        
        Args:
            task_type: 任务类型
            description: 用户描述
            parameters: 分析参数
            
        Returns:
            分析计划字典
        """
        try:
            # 从向量存储中获取相关上下文
            context = ""
            if self.vector_store:
                docs = self.vector_store.similarity_search(
                    f"{task_type} {description}",
                    k=3  # 获取最相关的3个文档片段
                )
                context = "\n".join([doc.page_content for doc in docs])
            
            # 执行LLM链
            response = self.analysis_chain.run(
                task_type=task_type,
                description=description,
                parameters=str(parameters),
                context=context
            )
            
            # 解析响应(简化版本，假设LLM已经返回格式化的JSON)
            import json
            try:
                analysis_plan = json.loads(response)
            except:
                self.logger.warning("LLM返回的不是有效JSON，返回原始文本")
                analysis_plan = {"raw_response": response}
            
            return analysis_plan
        except Exception as e:
            self.logger.error(f"解析请求失败: {str(e)}")
            raise e 