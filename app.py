import os
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict
from sentence_transformers import SentenceTransformer
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

os.environ["TOKENIZERS_PARALLELISM"] = "false"
uri = "YOUR_CONNECTION_STRING"

db_name = "YOUR_DB_NAME"
collection_name = "YOUR_COLLECTION_NAME"

elements = partition_pdf("mydocuments/Document2.pdf",
                         strategy="hi_res",
                         infer_table_structured=True)

records = convert_to_dict(elements)

model = SentenceTransformer('microsoft/mpnet-base')

emb = model.encode("this is a test").tolist()
# print(len(emb))
# print(emb[:10])
print("\n")

for record in records:
    txt = record['text']
    record['embedding'] = model.encode(txt).tolist()

# New client to connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# delete all first
client[db_name][collection_name].delete_many({})

# insert
client[db_name][collection_name].insert_many(records)
query = "Does the encoder contain self-attention layers?"

vector_query = model.encode(query).tolist()
print("The vector query==", vector_query)
print("\n")

pipeline = [
    {
        "$search": {
            "index": "default",
            "knnBeta": {
                "vector": vector_query,
                "path": "embedding",
                "k": 5,
            }
        }
    },
    {
        "$project": {
            "embedding": 0,
            "_id": 0,
            "score": {
                "$meta": "searchScore"
            },
        }
    }
]

results = list(client[db_name][collection_name].aggregate(pipeline))
