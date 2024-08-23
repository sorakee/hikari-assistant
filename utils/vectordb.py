from fast_sentence_transformers import FastSentenceTransformer as SentenceTransformer
import torch
import time


start = time.time()
print(torch.cuda.is_available())

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

sentences = [
    "The weather is lovely today.",
    "It's so sunny outside!",
    "He drove to the stadium.",
]
embeddings = model.encode(sentences)
print(embeddings.shape)

similarities = model.similarity(embeddings, embeddings)
print(similarities)
end = time.time()
print(end-start)