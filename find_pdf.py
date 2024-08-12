import os
# import time
# import params
from pymongo import MongoClient
from bson import ObjectId
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

mongodb_conn_string = os.getenv("mongodb_conn_string")
database = os.getenv("database")
collection = os.getenv("collection")
collection_final = os.getenv("collection_final")

mongo_client = MongoClient(mongodb_conn_string)
result_collection = mongo_client[database][collection]
result_collection_final = mongo_client[database][collection_final]
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
total_documents = result_collection_final.count_documents({})
desired_answers = 50

def rrf(rankings, k=60):
    scores = {}
    for rank, doc in enumerate(rankings, start=1):
        doc_id = doc['_id']
        score = 1 / (k + rank)
        if doc_id in scores:
            scores[doc_id] += score
        else:
            scores[doc_id] = score
    return scores

def search_candidates(jd):
    candidates = []
    query_vector = model.encode(jd).tolist()
    pipeline_document = [
        {
            "$vectorSearch": {
                "index": "default",
                "path": "documentVector",
                "queryVector": query_vector,
                "numCandidates": total_documents,
                "limit": desired_answers
            }
        }
    ]

    pipeline_collection = [
        {
            "$vectorSearch": {
                "index": "default",
                "path": "collectionVector",
                "queryVector": query_vector,
                "numCandidates": total_documents,
                "limit": desired_answers
            }
        }
    ]

    document_search_results = list(result_collection_final.aggregate(pipeline_document))
    collection_search_results = list(result_collection_final.aggregate(pipeline_collection))

    doc_rrf_scores = rrf(document_search_results)
    collection_rrf_scores = rrf(collection_search_results)

    combined_scores = {}
    for doc_id, score in doc_rrf_scores.items():
        combined_scores[doc_id] = score

    for doc_id, score in collection_rrf_scores.items():
        if doc_id in combined_scores:
            combined_scores[doc_id] += score
        else:
            combined_scores[doc_id] = score

    sorted_combined_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    final_results = sorted_combined_results[:desired_answers]

    unique_documents = []
    seen_documents = set()

    for doc_id, _ in final_results:
        if doc_id not in seen_documents:
            unique_documents.append(doc_id)
            seen_documents.add(doc_id)

    for doc_id in unique_documents:
        resume_data = result_collection_final.find_one({"_id": doc_id})
        resume_data = remove_object_ids(resume_data)
        if resume_data['assId'] is not None:
            candidates.append(remove_object_ids(resume_data["assId"]))
    print(candidates)
    return candidates

def remove_object_ids(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict):
                data[key] = remove_object_ids(value)
            elif isinstance(value, list):
                data[key] = [remove_object_ids(item) for item in value]
    elif isinstance(data, list):
        data = [remove_object_ids(item) for item in data]
    return data

search_candidates("Data Scientist with 2 years of experience in Python and Machine Learning")