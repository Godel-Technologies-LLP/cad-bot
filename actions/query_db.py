import faiss
import numpy as np
import json
from openai import OpenAI


def get_layer_name(
    input,
    index_file="./db/dxf_faiss_database.index",
    metadata_file="db/dxf_faiss_database_metadata.json",
    top_k=5,
):
    client = OpenAI()

    # Load the FAISS index
    index = faiss.read_index(index_file)

    # Load the metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    # Convert query to vector using OpenAI
    response = client.embeddings.create(input=input, model="text-embedding-3-small")
    query_vector = np.array([response.data[0].embedding], dtype=np.float32)

    # Search the index
    distances, indices = index.search(query_vector, top_k)

    # Return the results with metadata
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(metadata):  # Check if idx is valid
            layer_info = metadata[idx]
            result = {
                "distance": float(distances[0][i]),
                "layer_name": layer_info["name"],
                "entities": layer_info.get("entities", []),
            }
            results.append(result)

    return results[0]["layer_name"]
