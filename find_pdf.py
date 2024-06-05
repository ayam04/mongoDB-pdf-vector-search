from sentence_transformers import SentenceTransformer, util
import params
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description='Atlas Vector Search PDF Demo')
parser.add_argument('-q', '--question', help="The question to ask")
args = parser.parse_args()

query = args.question // enter the jd here

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

query_vector = model.encode(query).tolist()

mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

desired_answers = 3

pipeline = [
    {
        "$search": {
            "knnBeta": {
                "vector": query_vector,
                "path": "sentenceVector",
                "k": 15
            }
        }
    },
    {
        "$limit": desired_answers
    }
]

results = result_collection.aggregate(pipeline)

print("\nBest Matching PDF(s)")
print("----------------------------------------------------")

for result in results:
    print("PDF:     ", result['pdf'])
