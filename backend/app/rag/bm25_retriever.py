import jieba
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.rag.chunk_store import load_chunks

#把一段中文文本切成词列表
#bm25是基于关键词的检索方法，需要先分词
def tokenize(text:str)->list[str]:
    #jieba.lcut会把文本切成一个个词语
    #token.strip()去掉词语两端的空白，如果切出来的词语是空的，就过滤掉
    #如果文本是英文或者其他语言，jieba也能处理，但效果可能不如专门的分词工具
    return [token.strip() for token in jieba.lcut(text) if token.strip()]

class BM25Retriever:
    def __init__(self):
        self.documents=load_chunks()
        #把每一个chunk分好词之后放在tokenized_corpus里，形成一个二维列表，每个元素是一个chunk的词列表
        self.tokrnized_corpus=[
            tokenize(document.page_content)
            for document in self.documents
        ]
        #如果有文档就用分词后的预料创建BM25检索器
        #如果没有就设为NOne
        self.bm25=BM25Okapi(self.tokrnized_corpus) if self.tokrnized_corpus else None
        
#根据query做bm25分词检索
    def retrieve(self,query:str,top_k:int=5)->list[Document]:
        if not self.documents or self.bm25 is None:
            return []
        
        tokenized_query=tokenize(query)
        # 计算 query 和每个 chunk 的 BM25 分数
        # scores 的长度和 self.documents 一样
        # scores[i] 对应 self.documents[i] 的得分
        scores=self.bm25.get_scores(tokenized_query)
        
        # 按 BM25 分数从高到低排序，得到文档下标列表
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )
        
        results=[]
        
        for indec in ranked_indices[:top_k]:
            if scores[indec]<=0:
                continue
            document=self.documents[indec]
            document.metadata["bm25_score"]=scores[indec]
            results.append(document)
        return results
    
# 工厂函数：创建一个 BM25Retriever 实例
def build_bm25_retriever() -> BM25Retriever:
    return BM25Retriever()