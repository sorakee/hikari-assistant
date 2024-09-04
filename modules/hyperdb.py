import os
import gzip
import time
import pickle
import numpy as np
from pathlib import Path
# from sentence_transformers import SentenceTransformer
from fast_sentence_transformers import FastSentenceTransformer as SentenceTransformer
from .galaxy_brain_math_shit import (
    dot_product,
    adams_similarity,
    cosine_similarity,
    derridaean_similarity,
    euclidean_metric,
    hyper_SVM_ranking_algorithm_sort,
)

# Fast sentence transformers is 360% faster than sentence transformer
# Initialize the model here so it is quantized and optimized only once for that runtime
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")


def get_embedding(documents, key=None):
    texts = None
    if isinstance(documents, list):
        if isinstance(documents[0], dict):
            texts = []
            if isinstance(key, str):
                if "." in key:
                    key_chain = key.split(".")
                else:
                    key_chain = [key]
                for doc in documents:
                    for key in key_chain:
                        doc = doc[key]
                    texts.append(doc.replace("\n", " "))
            elif key is None:
                for doc in documents:
                    text = ", ".join([f"{key}: {value}" for key, value in doc.items()])
                    texts.append(text)
        elif isinstance(documents[0], str):
            texts = documents
    
    # Putting this line here increases time taken from 0.07s to 23s (32,757.14% worse WTF!)
    # model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    embeddings = model.encode(texts)

    return embeddings


class HyperDB:
    def __init__(
        self,
        documents=None,
        vectors=None,
        key=None,
        embedding_function=None,
        similarity_metric="cosine",
    ):
        print("\n##########")
        print("DATABASE INITIALIZED")
        print("##########\n")
        documents = documents or []
        self.documents = []
        self.vectors = None
        self.embedding_function = embedding_function or (
            lambda docs: get_embedding(docs, key=key)
        )
        if vectors is not None:
            self.vectors = vectors
            self.documents = documents
        else:
            self.add_documents(documents)

        if similarity_metric.__contains__("dot"):
            self.similarity_metric = dot_product
        elif similarity_metric.__contains__("cosine"):
            self.similarity_metric = cosine_similarity
        elif similarity_metric.__contains__("euclidean"):
            self.similarity_metric = euclidean_metric
        elif similarity_metric.__contains__("derrida"):
            self.similarity_metric = derridaean_similarity
        elif similarity_metric.__contains__("adams"):
            self.similarity_metric = adams_similarity
        else:
            raise Exception(
                "Similarity metric not supported. Please use either 'dot', 'cosine', 'euclidean', 'adams', or 'derrida'."
            )

    def dict(self, vectors=False):
        if vectors:
            return [
                {"document": document, "vector": vector.tolist(), "index": index}
                for index, (document, vector) in enumerate(
                    zip(self.documents, self.vectors)
                )
            ]
        return [
            {"document": document, "index": index}
            for index, document in enumerate(self.documents)
        ]

    def add(self, documents, vectors=None):
        if not isinstance(documents, list):
            return self.add_document(documents, vectors)
        self.add_documents(documents, vectors)

    def add_document(self, document: dict, vector=None):
        vector = (
            vector if vector is not None else self.embedding_function([document])[
                0]
        )
        # print(vector.shape)
        # print(vector.ndim)
        # Delete these two lines if you are not using 
        # "fast-sentence-transformer" for some reason
        if vector.ndim == 2:
            vector = vector.flatten()
            # print(vector.shape)
        if self.vectors is None:
            self.vectors = np.empty((0, len(vector)), dtype=np.float32)
        elif len(vector) != self.vectors.shape[1]:
            raise ValueError("All vectors must have the same length.")
        self.vectors = np.vstack([self.vectors, vector]).astype(np.float32)
        self.documents.append(document)

    def remove_document(self, index):
        self.vectors = np.delete(self.vectors, index, axis=0)
        self.documents.pop(index)

    def add_documents(self, documents, vectors=None):
        if not documents:
            return
        vectors = vectors or np.array(self.embedding_function(documents)).astype(
            np.float32
        )
        for vector, document in zip(vectors, documents):
            self.add_document(document, vector)

    def save(self, storage_file):
        if self.vectors is None or self.documents is None:
            return
        
        file_path = Path(storage_file)
        directory = file_path.parent

        if not os.path.exists(directory):
            os.mkdir(directory)

        data = {"vectors": self.vectors, "documents": self.documents}
        if storage_file.endswith(".gz"):
            with gzip.open(storage_file, "wb") as f:
                pickle.dump(data, f)
        else:
            with open(storage_file, "wb") as f:
                pickle.dump(data, f)
        print("\n##########")
        print("DOCUMENTS SAVED TO DATABASE")
        print("##########\n")

    def load(self, storage_file):
        if storage_file.endswith(".gz"):
            with gzip.open(storage_file, "rb") as f:
                data = pickle.load(f)
        else:
            with open(storage_file, "rb") as f:
                data = pickle.load(f)
        print("\n##########")
        print("LOADED DOCUMENTS FROM DATABASE")
        print("##########\n")
        self.vectors = data["vectors"].astype(np.float32)
        self.documents = data["documents"]

    def query(self, query_text, top_k=1, return_similarities=True):
        if self.vectors is None:
            return []

        query_vector = self.embedding_function([query_text])[0]
        ranked_results, similarities = hyper_SVM_ranking_algorithm_sort(
            self.vectors, query_vector, top_k=top_k, metric=self.similarity_metric
        )
        
        # print(ranked_results)

        if return_similarities:
            return list(
                zip([self.documents[index]
                     for index in ranked_results], similarities)
            )

        result = []
        if top_k == 1:
            # Retrieve the message before and after the current message as well
            for i in [-1, 0, 1]:
                try:
                    if ranked_results[0] + i >= 0:
                        result.append(self.documents[ranked_results[0] + i])
                except IndexError:
                    # Skips this index if out of bounds
                    continue
        else:
            result = [self.documents[index] for index in ranked_results]

        return result

    def similar_vectors(self, vector, top_k=1, return_similarities=True):
        if self.vectors is None:
            return []

        ranked_results, similarities = hyper_SVM_ranking_algorithm_sort(
            self.vectors, vector, top_k=top_k, metric=self.similarity_metric
        )
        if return_similarities:
            return list(
                zip([self.documents[index] for index in ranked_results], similarities)
            )
        return [self.documents[index] for index in ranked_results]


if __name__ == "__main__":
    start = time.time()
    # Fill documents with example sentences generated by ChatGPT (GPT-4o)
    documents = [
        "User: Hikari, remind me later that I have to go meet up with my friends at Piccadilly Gardens tomorrow afternoon.",
        "Hikari: Okay~! I'll make sure to remind you to visit your friends tomorrow afternoon. You'll have such a great time catching up with them! If you need any help planning your visit or need more reminders, just let me know, okay?",
        "User: How are you doing today, Hikari?",
        "Hikari: Aww, you're so sweet for asking! 💖 I'm doing great, especially now that I'm chatting with you! How about you? Anything exciting or fun planned for today? I'm here to make your day even brighter!",
        "User: I am planning to continue yesterday's programming work and try to finish it by tomorrow.",
        "Hikari: That sounds like a productive plan! I'm sure you'll do an amazing job! If you need any help or just want to take a break and chat, I'm right here cheering you on! Let's make sure you finish it by tomorrow so you can celebrate your hard work! Goodluck~! 💪"
    ]

    # Instantiate HyperDB with the list of documents
    db = HyperDB(documents)

    # Save the HyperDB instance to a file
    db.save("db/hikari.pickle.gz")

    # Load the HyperDB instance from the save file
    db.load("db/hikari.pickle.gz")

    # Query the HyperDB instance with a text input
    results = db.query("Hikari, do you remember what I planned to do and what by time should I finish it?", return_similarities=False)
    print(results)

    # Print the query results
    for r in results:
        print(r)

    end = time.time()
    print(f"Elapsed time: {end - start}")

    # start = time.time()
    # model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu").encode("This is a test", device="cpu", show_progress_bar=True)
    # end = time.time()
    # print(f"Elapsed time: {end - start}")