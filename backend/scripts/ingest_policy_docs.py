from app.rag import ingest_policy_documents


if __name__ == "__main__":
    count = ingest_policy_documents()
    print(f"Ingested {count} policy chunks into local Chroma.")