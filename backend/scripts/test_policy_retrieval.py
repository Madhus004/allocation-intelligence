from app.rag import retrieve_policy_context_as_text


if __name__ == "__main__":
    query = (
        "allocation override store protection high velocity "
        "replenishment risk promise risk weather capacity"
    )
    result = retrieve_policy_context_as_text(query=query, k=3)
    print(result)