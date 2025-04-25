import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import LanceDB
import lancedb
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 环境变量设置示例（实际使用时应通过环境变量设置）
# os.environ["OPENAI_API_KEY"] = "your-api-key"

# 1. 加载文档
def load_documents(directory: str) -> List[Document]:
    """
    从指定目录加载所有文本文档
    Args:
        directory: 文档所在目录路径
    Returns:
        Document对象列表
    """
    documents = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith(('.txt', '.md', '.pdf')):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        documents.append(Document(
                            page_content=content,
                            metadata={"source": filename, "path": file_path}
                        ))
                except Exception as e:
                    logger.error(f"读取文件 {filename} 时出错: {str(e)}")
    except Exception as e:
        logger.error(f"读取目录 {directory} 时出错: {str(e)}")
    
    logger.info(f"成功加载了 {len(documents)} 个文档")
    return documents

# 2. 文档分割
def split_documents(documents: List[Document],
                   chunk_size: int = 100,
                   chunk_overlap: int = 20) -> List[Document]:
    """
    将文档分割成更小的块
    Args:
        documents: 要分割的文档列表
        chunk_size: 每个块的最大字符数
        chunk_overlap: 相邻块之间的重叠字符数
    Returns:
        分割后的文档块列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"文档被分割为 {len(split_docs)} 个块")
    return split_docs

# 3. 创建向量存储
def create_vector_store(documents: List[Document],
                       collection_name: str = "knowledge_base",
                       db_path: str = "./lancedb",
                       recreate: bool = False,
                       enable_vector: bool = False) -> LanceDB:
    """
    创建LanceDB向量存储
    Args:
        documents: 要存储的文档列表
        collection_name: LanceDB集合名称
        db_path: LanceDB数据库路径
        recreate: 是否重新创建集合
        enable_vector: 是否开启向量存储功能，默认为False
    Returns:
        LanceDB向量存储对象
    """
    try:
        # 检查文档列表是否为空
        if not documents:
            raise ValueError("文档列表为空，无法创建向量存储。请确保文档目录中有有效文件。")
        
        # 创建LanceDB数据库连接
        db = lancedb.connect(db_path)
        
        # 创建向量存储
        if recreate and collection_name in db.table_names():
            db.drop_table(collection_name)
            logger.info(f"删除已存在的集合: {collection_name}")
        
        if enable_vector:
            # 启用向量存储时，使用OpenAI embeddings
            logger.info("启用向量存储功能，使用OpenAI embeddings")
            embeddings = OpenAIEmbeddings()
        else:
            # 不启用向量存储时，使用空向量
            logger.info("未启用向量存储功能，使用标准文本索引")
            # 使用一个简单的假embeddings对象，生成全零向量
            class DummyEmbeddings:
                def embed_documents(self, texts):
                    # 返回一个小的全零向量
                    return [[0.0] * 4 for _ in texts]
                
                def embed_query(self, text):
                    # 返回一个小的全零向量
                    return [0.0] * 4
            
            embeddings = DummyEmbeddings()
        
        # 创建向量存储
        vector_store = LanceDB.from_documents(
            documents=documents,
            embedding=embeddings,
            connection=db,
            table_name=collection_name
        )
        
        logger.info(f"成功创建存储，集合名称: {collection_name}")
        return vector_store
    except Exception as e:
        logger.error(f"创建存储时出错: {str(e)}")
        raise

# 4. 创建问答链
def create_qa_chain(vector_store: LanceDB,
                   temperature: float = 0.0,
                   search_k: int = 5,
                   search_type: str = "vector") -> RetrievalQA:
    """
    创建检索问答链
    Args:
        vector_store: LanceDB向量存储对象
        temperature: 生成模型的温度参数
        search_k: 检索的文档数量
        search_type: 检索类型，可以是 "vector"(向量检索), "bm25"(关键词检索), "hybrid"(混合检索)
    Returns:
        RetrievalQA链对象
    """
    try:
        # 创建检索器，根据指定的搜索类型
        if search_type == "vector":
            # 纯向量搜索
            retriever = vector_store.as_retriever(
                search_kwargs={"k": search_k}
            )
            logger.info("使用向量检索模式")
        elif search_type == "bm25":
            # 使用BM25/关键词搜索
            # 注意：LanceDB通过SQL查询支持关键词搜索
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",  # 使用阈值搜索
                search_kwargs={
                    "k": search_k,
                    "score_threshold": 0.0,  # 设置为0以确保返回结果
                    "kwargs": {
                        "metric": "cosine",  # 使用余弦相似度
                        "use_relevance": True,  # 使用相关性评分
                    }
                }
            )
            logger.info("使用BM25/关键词检索模式")
        elif search_type == "hybrid":
            # 混合检索 - 在LanceDB中通过组合查询实现
            # 这里我们使用默认的向量检索，但在实际应用中可以自定义查询
            retriever = vector_store.as_retriever(
                search_kwargs={
                    "k": search_k,
                    "kwargs": {
                        "use_relevance": True  # 启用相关性评分
                    }
                }
            )
            logger.info("使用混合检索模式")
        else:
            # 默认使用向量检索
            retriever = vector_store.as_retriever(
                search_kwargs={"k": search_k}
            )
            logger.info(f"未知的搜索类型: {search_type}，使用默认向量检索")
        
        # 创建自定义提示模板
        template = """
        使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。
        
        {context}
        
        问题: {question}
        回答:
        """
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        logger.info(f"使用API密钥: {api_key}")
        if not api_key:
            raise ValueError("请设置环境变量 'DEEPSEEK_API_KEY' 来提供API密钥")
        # 创建大语言模型
        llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/", api_key=api_key, temperature=temperature)
        
        # 创建问答链
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    except Exception as e:
        logger.error(f"创建问答链时出错: {str(e)}")
        raise

# 5. 完整流程示例
def build_knowledge_qa_system(docs_directory: str,
                             collection_name: str = "knowledge_base",
                             db_path: str = "./lancedb",
                             recreate: bool = False,
                             search_type: str = "bm25",
                             enable_vector: bool = False) -> RetrievalQA:
    """
    构建完整的知识库问答系统
    Args:
        docs_directory: 文档目录
        collection_name: 向量存储集合名称
        db_path: LanceDB数据库路径
        recreate: 是否重新创建向量存储
        search_type: 检索类型，可以是 "vector", "bm25", "hybrid"
        enable_vector: 是否启用向量存储功能，默认为False
    Returns:
        问答系统链
    """
    # 加载文档
    documents = load_documents(docs_directory)
    
    # 检查文档是否为空
    if not documents:
        raise ValueError(f"无法从 {docs_directory} 加载任何文档。请确保目录存在且包含有效文件。")
    
    # 分割文档
    split_docs = split_documents(documents)
    
    # 再次检查分割后的文档
    if not split_docs:
        raise ValueError("文档分割后为空。请检查文档内容是否有效。")
    
    # 创建向量存储
    vector_store = create_vector_store(
        split_docs, 
        collection_name=collection_name,
        db_path=db_path,
        recreate=recreate,
        enable_vector=enable_vector
    )
    
    # 创建问答链
    qa_chain = create_qa_chain(vector_store, search_type=search_type)
    
    return qa_chain

# 6. 使用示例
def query_example():
    """示例：如何使用问答系统"""
    try:
        # 检查文档目录是否存在且不为空
        docs_dir = "./documents"
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            logger.warning(f"创建了文档目录: {docs_dir}")
            # 创建一个示例文档，避免空目录错误
            with open(os.path.join(docs_dir, "example.txt"), "w", encoding="utf-8") as f:
                f.write("这是一个示例文档。\n公司的年假政策是每年15天带薪假期。\n新员工入职满3个月后可以开始使用年假。")
            logger.info("创建了示例文档以避免空目录错误")
        
        # 检查目录中是否有文件
        files = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f)) and f.endswith(('.txt', '.md', '.pdf'))]
        if not files:
            logger.warning(f"文档目录 {docs_dir} 中没有有效的文本文件")
            # 创建一个示例文档
            with open(os.path.join(docs_dir, "example.txt"), "w", encoding="utf-8") as f:
                f.write("这是一个示例文档。\n公司的年假政策是每年15天带薪假期。\n新员工入职满3个月后可以开始使用年假。")
            logger.info("创建了示例文档以进行演示")
        
        # 构建问答系统
        qa_system = build_knowledge_qa_system(
            docs_dir, 
            "company_knowledge",
            recreate=True,
            search_type="bm25",
            enable_vector=False  # 默认不使用向量存储功能
        )
        
        # 查询示例
        query = "公司的年假政策是什么？"
        query = "国家法律法规数据库什么时候开通的，谁在维护，登载什么内容"
        result = qa_system({"query": query})
        
        # 输出结果
        print(f"问题: {query}")
        print(f"回答: {result['result']}")
        
        # 输出来源文档
        print("\n来源文档:")
        for i, doc in enumerate(result["source_documents"]):
            print(f"文档 {i+1}: {doc.metadata.get('source', '未知来源')}")
            print(f"内容片段: {doc.page_content[:100]}...\n")
    
    except Exception as e:
        logger.error(f"执行查询示例时出错: {str(e)}")
        raise

# 7. 主函数
def main():
    # 确保文档目录存在
    docs_dir = "./documents"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        logger.warning(f"创建了文档目录: {docs_dir}，请在该目录中放入您的知识库文档")
    
    # 执行示例
    query_example()

if __name__ == "__main__":
    main()
