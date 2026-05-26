import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    #清除非法的unicode字符
    text = text.encode("utf-8", errors="ignore").decode("utf-8")

    #统一换行符
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    
    #替换不常见的空白字符为普通空格
    text = text.replace("\u00a0", " ") #不间断空格
    text = text.replace("\t", " ") #制表符

    # 合并中文 PDF 断行，比如 “随\n机\n变\n量”
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s*\n\s*(?=[\u4e00-\u9fff])", "", text)

    # 合并普通多余空格
    text = re.sub(r"[ ]{2,}", " ", text)

    # 去掉过多空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


#判断文本块是否有效
#1. 空文本
#2. 太短的文本
#3. 几乎没有中文、英文、数字的噪声文本
def is_valid_chunk(text: str) -> bool:
    if not text:
        return False
    
    if is_toc_like(text):
        return False
    
    text = text.strip()

    if len(text) < 30:
        return False

    # 如果几乎没有中文、英文、数字，通常是 PDF 噪声
    useful_chars = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text)
    if len(useful_chars) < 10:
        return False
    
    symbol_chars = re.findall(r"[^\u4e00-\u9fffA-Za-z0-9\s，。！？；：、（）()\[\]{}.,!?;:+\-*/=<>≤≥]", text)

    if len(useful_chars) < 30 and len(symbol_chars) > 20:   
        return False

    return True

#判断chunk是不是目录页
def is_toc_like(text: str) -> bool:
    section_count = text.count("第一节") + text.count("第二节") + text.count("第三节") + text.count("第四节") + text.count("第五节")
    return section_count >= 3 and len(text) < 300