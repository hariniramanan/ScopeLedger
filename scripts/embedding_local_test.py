from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)

dimension = model.get_sentence_embedding_dimension()

print()
print("Model:", MODEL_NAME)
print("Embedding dimension:", dimension)


text = (
    "The client confirmed that the September 30 "
    "launch deadline remains unchanged."
)

embedding = model.encode(
    text,
    normalize_embeddings=True,
)


print("Generated vector length:", len(embedding))

print()
print("First 5 values:")
print(embedding[:5])