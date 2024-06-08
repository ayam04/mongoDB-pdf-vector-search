from sentence_transformers import SentenceTransformer
import params
from pymongo import MongoClient

with open("jd.txt", "r") as file: #enter jd here 
    jd = file.read()

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

query_vector = model.encode(jd).tolist()
mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

desired_answers = 3

#pipeline for vector search index

pipeline = [ 
    {
    "$vectorSearch": {
      "index": "vector_index", 
      "path": "documentVector", 
      "queryVector": query_vector,
      "numCandidates": 150,
      "limit": 10
    }
   }
]

#pipeline for normal search index

# pipeline = [
#   {
#     "$search": {
#       "index": "default",
#       "text": {
#         "query": query,
#         "path": {
#           "wildcard": "*",
#         },
#       },
#     },
#   },
#   {
#     "$limit": 3
#   }
# ]

results = result_collection.aggregate(pipeline)

print("\nBest Matching PDF(s)")
print("----------------------------------------------------")

for i in results:
    print("PDF: ", i["resumeData"]["resumeName"] or i["pdf"])