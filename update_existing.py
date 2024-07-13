import params
import certifi
from pymongo import MongoClient
import time
from sentence_transformers import SentenceTransformer
from functions import clean_text

mongo_client = MongoClient(params.mongodb_conn_string, tlsCAFile=certifi.where())
result_collection = mongo_client[params.database][params.collection]

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def dict_to_string(d, exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = ["resumeName", "jdMatchScore", "jdMatchScoreUI"]

    result = []

    def recursive_items(d, parent_key=''):
        for k, v in d.items():
            new_key = f"{parent_key}{k}" if parent_key else k
            if new_key in exclude_keys:
                continue
            if isinstance(v, dict):
                recursive_items(v, new_key + ' ')
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        recursive_items(item, new_key + ' ')
                    else:
                        if item:
                            result.append(f"{new_key}: {item}")
            else:
                if v not in [None, '', [], {}]:
                    result.append(f"{new_key}: {v}")

    recursive_items(d)
    return ' '.join(result)

def update_existing():
    start = time.time()
    documents = result_collection.find({"documentVector": {"$exists": False}})
    for document in documents:
        try:
            resume_data = document.get('resumeData', {})
            resume_text = dict_to_string(resume_data)
            # print(resume_text)
            document_vector = model.encode(resume_text).tolist()

            result_collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"documentVector": document_vector}}
            )
            print(f"Updated doc: {document['_id']}")
        except Exception as e:
            print(f"Error with: {document['_id']}: {e}")
            continue
    stop = time.time()
    print(f"Time taken: {stop-start}")

update_existing()