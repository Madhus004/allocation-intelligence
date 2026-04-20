from pathlib import Path
from typing import List
from app import config  # ensures project-specific .env is loaded

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_DOCS_DIR = BASE_DIR / "policy_docs"
CHROMA_DIR = BASE_DIR / "data" / "chroma_policy_db"
COLLECTION_NAME = "oms_policy_docs"


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings()


def _get_vectorstore() -> Chroma:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def load_policy_documents() -> List[Document]:
    docs: List[Document] = []

    for path in POLICY_DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "doc_type": "policy",
                },
            )
        )

    return docs


def chunk_policy_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    return splitter.split_documents(documents)


def ingest_policy_documents() -> int:
    documents = load_policy_documents()
    if not documents:
        raise ValueError(f"No policy documents found in {POLICY_DOCS_DIR}")

    chunks = chunk_policy_documents(documents)
    vectorstore = _get_vectorstore()

    # clear and rebuild for prototype simplicity
    existing = vectorstore.get()
    ids = existing.get("ids", [])
    if ids:
        vectorstore.delete(ids=ids)

    vectorstore.add_documents(chunks)
    return len(chunks)


def retrieve_policy_context(query: str, k: int = 3) -> List[Document]:
    vectorstore = _get_vectorstore()
    return vectorstore.similarity_search(query, k=k)


def retrieve_policy_context_as_text(query: str, k: int = 3) -> str:
    docs = retrieve_policy_context(query=query, k=k)
    if not docs:
        return "No relevant policy context found."

    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Policy Chunk {i} | Source: {source}]\n{doc.page_content}")

    return "\n\n".join(parts)