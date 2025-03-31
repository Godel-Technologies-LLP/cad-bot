import faiss
import numpy as np
import json
import pandas as pd


def create_faiss_database_local(vectors_file, layers_file, entities_file, output_file):
    try:
        # 5. Load vectors for layer descriptions
        vectors = np.load(vectors_file)

        # 1 & 2. Load layer names and descriptions
        layers_df = pd.read_csv(layers_file)

        # 3 & 4. Load entities and their descriptions
        with open(entities_file, 'r') as f:
            entities_by_layer = json.load(f)

        # Create a FAISS index for the vectors
        vector_dimension = vectors.shape[1]  # Get the dimension of the vectors
        index = faiss.IndexFlatL2(vector_dimension)

        # Create a mapping between FAISS indices and layer information
        metadata = []
        for i, row in layers_df.iterrows():
            layer_data = row.to_dict()

            # Add entities for this layer if available
            if row['name'] in entities_by_layer:
                layer_data['entities'] = entities_by_layer[row['name']]
            else:
                layer_data['entities'] = []

            metadata.append(layer_data)

        # Save metadata alongside the index using IndexIDMap
        index_with_ids = faiss.IndexIDMap(index)
        for i in range(len(vectors)):
            index_with_ids.add_with_ids(np.array([vectors[i]]), np.array([i]))

        # Save the combined index
        faiss.write_index(index_with_ids, output_file + ".index")

        # Still need to save metadata separately as FAISS doesn't store arbitrary metadata
        with open(output_file + "_metadata.json", 'w') as f:
            json.dump(metadata, f, default=str)

        return True
    except Exception as e:
        print(f"Error creating FAISS database: {str(e)}")
        return False


def search_faiss_database_local(query_text, index_file, metadata_file, client, top_k=5):
    # Load the FAISS index
    index = faiss.read_index(index_file)

    # Load the metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Convert query to vector using OpenAI
    response = client.embeddings.create(
        input=query_text,
        model="text-embedding-3-small"
    )
    query_vector = np.array([response.data[0].embedding], dtype=np.float32)

    # Search the index
    distances, indices = index.search(query_vector, top_k)

    # Return the results with metadata
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(metadata):  # Check if idx is valid
            result = {
                "distance": float(distances[0][i]),
                "layer_info": metadata[idx]
            }
            results.append(result)

    return results


# Usage example
vectors_file = "processed_data_vectors.npy"
layers_file = "processed_data_layers.csv"
entities_file = "processed_data_entities.json"
output_file = "dxf_faiss_database"

success = create_faiss_database_local(vectors_file, layers_file, entities_file, output_file)

if success:
    print("FAISS database created successfully.")
else:
    print("Failed to create FAISS database.")
