"""Write document loaders here."""
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_core.documents import Document

def load_document(path:str|Path)->list[Document]:
    path=Path(path)
    suffix=path.suffix.lower()
    
    if suffix==".pdf":
        loader=PyPDFLoader(str(path))
        return loader.load()

    if suffix in [".txt",".md"]:
        loader=TextLoader(str(path),encoding="utf-8")
        return loader.load()
    raise ValueError(f"Unsupported file type: {suffix}")