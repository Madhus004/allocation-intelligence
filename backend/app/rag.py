from pathlib import Path
from typing import List

from sqlalchemy import text

from app import config
from app.db import engine

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_DOCS_DIR = BASE_DIR / "policy_docs"
COLLECTION_NAME = "oms_policy_docs"


def _get_embeddings() -> OpenAIEmbeddings:
    config.validate_openai_config()
    return OpenAIEmbeddings(model=config.OPENAI_EMBEDDING_MODEL)


def _get_chroma_dir() -> Path:
    chroma_dir = Path(config.CHROMA_PERSIST_DIR)
    if not chroma_dir.is_absolute():
        chroma_dir = BASE_DIR / chroma_dir
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chroma_dir


def _get_chroma_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_get_embeddings(),
        persist_directory=str(_get_chroma_dir()),
    )


def load_policy_documents() -> List[Document]:
    docs: List[Document] = []

    for path in POLICY_DOCS_DIR.glob("*.md"):
        text_content = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text_content,
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


def _ingest_policy_documents_chroma(chunks: List[Document]) -> int:
    vectorstore = _get_chroma_vectorstore()

    existing = vectorstore.get()
    ids = existing.get("ids", [])
    if ids:
        vectorstore.delete(ids=ids)

    vectorstore.add_documents(chunks)
    return len(chunks)


def _ingest_policy_documents_supabase(chunks: List[Document]) -> int:
    embeddings = _get_embeddings()
    contents = [chunk.page_content for chunk in chunks]
    vectors = embeddings.embed_documents(contents)

    with engine.begin() as conn:
        conn.execute(text(f"delete from {config.SUPABASE_VECTOR_TABLE}"))

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors), start=1):
            source = chunk.metadata.get("source", "unknown")
            doc_type = chunk.metadata.get("doc_type", "policy")
            vector_str = "[" + ",".join(str(x) for x in vector) + "]"

            conn.execute(
                text(
                    f"""
                    insert into {config.SUPABASE_VECTOR_TABLE}
                    (source, doc_type, chunk_index, content, embedding)
                    values
                    (:source, :doc_type, :chunk_index, :content, CAST(:embedding AS vector))
                    """
                ),
                {
                    "source": source,
                    "doc_type": doc_type,
                    "chunk_index": idx,
                    "content": chunk.page_content,
                    "embedding": vector_str,
                },
            )

    return len(chunks)


def ingest_policy_documents() -> int:
    documents = load_policy_documents()
    if not documents:
        raise ValueError(f"No policy documents found in {POLICY_DOCS_DIR}")

    chunks = chunk_policy_documents(documents)

    provider = config.VECTOR_STORE_PROVIDER.lower()
    if provider == "chroma":
        return _ingest_policy_documents_chroma(chunks)
    if provider == "supabase":
        return _ingest_policy_documents_supabase(chunks)

    raise ValueError(f"Unsupported VECTOR_STORE_PROVIDER: {config.VECTOR_STORE_PROVIDER}")


def _retrieve_policy_context_chroma(query: str, k: int = 3) -> List[Document]:
    vectorstore = _get_chroma_vectorstore()
    return vectorstore.similarity_search(query, k=k)


def _retrieve_policy_context_supabase(query: str, k: int = 3) -> List[Document]:
    embeddings = _get_embeddings()
    query_vector = embeddings.embed_query(query)
    vector_str = "[" + ",".join(str(x) for x in query_vector) + "]"

    sql = text(
        f"""
        select
            source,
            doc_type,
            chunk_index,
            content
        from {config.SUPABASE_VECTOR_TABLE}
        order by embedding <-> CAST(:query_embedding AS vector)
        limit :limit
        """
    )

    docs: List[Document] = []
    with engine.begin() as conn:
        rows = conn.execute(
            sql,
            {
                "query_embedding": vector_str,
                "limit": k,
            },
        ).fetchall()

    for row in rows:
        docs.append(
            Document(
                page_content=row.content,
                metadata={
                    "source": row.source,
                    "doc_type": row.doc_type,
                    "chunk_index": row.chunk_index,
                },
            )
        )

    return docs


def retrieve_policy_context(query: str, k: int = 3) -> List[Document]:
    provider = config.VECTOR_STORE_PROVIDER.lower()
    if provider == "chroma":
        return _retrieve_policy_context_chroma(query=query, k=k)
    if provider == "supabase":
        return _retrieve_policy_context_supabase(query=query, k=k)

    raise ValueError(f"Unsupported VECTOR_STORE_PROVIDER: {config.VECTOR_STORE_PROVIDER}")


def retrieve_policy_context_as_text(query: str, k: int = 3) -> str:
    docs = retrieve_policy_context(query=query, k=k)
    if not docs:
        return "No relevant policy context found."

    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Policy Chunk {i} | Source: {source}]\n{doc.page_content}")

    return "\n\n".join(parts)