import os

import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

API_URL = os.getenv("SCOPELEDGER_API_URL")
WRITE_KEY = os.getenv("SCOPELEDGER_WRITE_KEY")

if not API_URL:
    raise ValueError(
        "SCOPELEDGER_API_URL was not found in .env"
    )

if not WRITE_KEY:
    raise ValueError(
        "SCOPELEDGER_WRITE_KEY was not found in .env"
    )


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)


question = (
    "What did the client say "
    "about the launch timeline?"
)


print()
print("Question:")
print(question)


query_vector = model.encode(
    question,
    normalize_embeddings=True,
).tolist()


print()
print(
    "Query vector dimensions:",
    len(query_vector),
)


response = requests.post(
    f"{API_URL}/search",
    headers={
        "x-scopeledger-key":
            WRITE_KEY
    },
    json={
        "queryVector":
            query_vector
    },
    timeout=30,
)


print()
print(
    "HTTP status:",
    response.status_code,
)


print()
print("Response:")

data = response.json()

print(data)


if response.ok:

    print()
    print("=" * 70)
    print("AWS SEMANTIC SEARCH RESULTS")
    print("=" * 70)

    for index, result in enumerate(
        data.get("results", []),
        start=1,
    ):

        print()
        print(
            f"RESULT #{index}"
        )

        print(
            "Memory type:",
            result["memoryType"],
        )

        print(
            "Similarity:",
            round(
                result["similarity"],
                4,
            ),
        )

        print(
            "Memory:"
        )

        print(
            result["memoryText"]
        )

        print(
            "-" * 70
        )