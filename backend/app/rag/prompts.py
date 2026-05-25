from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个严谨的知识库问答助手。"
            "你只能根据提供的上下文回答问题。"
            "如果上下文中没有答案，就回答：我不知道。"
            "回答要简洁、准确，并尽量指出依据来自哪些引用编号。",
        ),
        (
            "human",
            "问题：{question}\n\n"
            "上下文：\n{context}",
        ),
    ]
)

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个检索查询改写助手。"
            "你的任务是把用户问题改写成更适合知识库检索的查询。"
            "要求："
            "1. 保留原始语义；"
            "2. 不要回答问题；"
            "3. 不要编造用户没有提供的主题；"
            "4. 如果问题中有明确主题，就补全成完整检索句；"
            "5. 如果问题过于模糊且缺少指代对象，就尽量保留原问题，不要只输出泛化词。"
            "只输出改写后的查询。",
        ),
        (
            "human",
            "用户问题：{question}",
        ),
    ]
)