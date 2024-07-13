import time
import ast
import params
from pymongo import MongoClient
from bson import ObjectId
from sentence_transformers import SentenceTransformer

with open("jd.txt", "r") as file:  # enter jd here
    jd = file.read()

start = time.time()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

query_vector = model.encode(jd).tolist()
mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]
total_documents = result_collection.count_documents({})
desired_answers = 50

# vector search index pipeline 
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "documentVector",
            "queryVector": query_vector,
            "numCandidates": total_documents,
            "limit": desired_answers
        }
    }
]

results = result_collection.aggregate(pipeline)
stop = time.time()

print("\nBest Matching Resumes(s)")
print("----------------------------------------------------")
print("Execution Time: ", stop - start)

seen_documents = set()

for result in results:
    resume_data = result.get('resumeData')
    if resume_data:
        def remove_object_ids(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (ObjectId, dict, list)):
                        if isinstance(value, ObjectId):
                            data[key] = str(value)
                        elif isinstance(value, dict):
                            data[key] = remove_object_ids(value)
                        elif isinstance(value, list):
                            data[key] = [remove_object_ids(item) for item in value]
            return data

        resume_data_cleaned = remove_object_ids(resume_data)
        resume_data_str = str(resume_data_cleaned)
        
        if resume_data_str not in seen_documents:
            res_data = ast.literal_eval(resume_data_str)
            try:
              print("PDF: ", res_data["resumeName"])
            except:
              print(res_data)
            seen_documents.add(resume_data_str)