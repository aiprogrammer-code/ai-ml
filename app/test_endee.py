from endee import Endee
import random

# Connect to local Endee server (default: localhost:8080)
client = Endee()

index_name = "resume_index"

# Step 1: Create index
try:
    client.create_index(
        name=index_name,
        dimension=4,
        space_type="cosine"
    )
    print(f"Index '{index_name}' created successfully.")
except Exception as e:
    print(f"Index may already exist or creation failed: {e}")

# Step 2: Get index handle
index = client.get_index(index_name)

# Step 3: Insert sample vectors
records = [
    {
        "id": "1",
        "vector": [0.1, 0.2, 0.3, 0.4],
        "meta": {
            "text": "Java Spring Boot Microservices developer with AWS experience",
            "source": "resume"
        },
        "filter": {
            "type": "resume"
        }
    },
    {
        "id": "2",
        "vector": [0.11, 0.19, 0.29, 0.41],
        "meta": {
            "text": "Backend developer skilled in Java, REST APIs, Docker, Kubernetes",
            "source": "resume"
        },
        "filter": {
            "type": "resume"
        }
    },
    {
        "id": "3",
        "vector": [0.9, 0.8, 0.7, 0.6],
        "meta": {
            "text": "Frontend React developer with UI and CSS expertise",
            "source": "resume"
        },
        "filter": {
            "type": "resume"
        }
    }
]

index.upsert(records)
print("Vectors inserted successfully.")

# Step 4: Search similar vectors
query_vector = [0.1, 0.2, 0.3, 0.39]
results = index.query(vector=query_vector, top_k=2)

print("\nSearch Results:")
print(results)