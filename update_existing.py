import params
import certifi
from pymongo import MongoClient
import time
from sentence_transformers import SentenceTransformer
from functions import clean_text
from bson import ObjectId
from upload_files import download_and_process_resume, delete_pdf
import os

mongodb_conn_string = os.getenv("mongodb_conn_string")
database = os.getenv("database")
collection = os.getenv("collection")
collection_vec = os.getenv("collection_vec")
collection_final = os.getenv("collection_final")

mongo_client = MongoClient(mongodb_conn_string, tlsCAFile=certifi.where())
result_collection = mongo_client[database][collection]
result_collection_vec = mongo_client[database][collection_vec]
result_collection_final = mongo_client[database][collection_final]

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def dict_to_string(d, exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = ["jdMatchScore", "jdMatchScoreUI", "documentVector"]

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

pipeline =   [
  {
    "$lookup": {
      "from": "companies",
      "localField": "companyId",
      "foreignField": "_id",
      "as": "companyDetails"
    }
  },
  {
    "$lookup": {
      "from": "jobs",
      "localField": "jobId",
      "foreignField": "_id",
      "as": "jobDetails"
    }
  },
  {
    "$match": {
      "$and": [
        { "companyDetails": { "$ne": [] } },
        { "jobDetails": { "$ne": [] } }
      ]
    }
  }
]

def create_final_vecs():
    files = []
    resuls = result_collection.aggregate(pipeline, maxTimeMS=600000, allowDiskUse=True)
    count_res = 0
    # print(len(resuls))
    for result in resuls:
        collectionVector = model.encode(dict_to_string(result).strip()).tolist()
        # count_res += 1
        # print(count_res)

        try:
            companyId = result['companyId']
            jobId = result['jobId']
            resumeData = result['resumeData']
            try:
                res_name = result['resumeData']["resumeName"]
                vec_resume = result_collection_vec.find({"resumeName": res_name})
                    
                if vec_resume:
                    count=0
                    for res in vec_resume:
                        documentVector = res['documentVector']
                        resumeText = res['resumeText']
                        count+=1
                        if count==1:
                            break
                
                files.append({
                    "companyId": companyId,
                    "jobId": jobId,
                    "resumeName": res_name,
                    "resumeData": resumeData,
                    "resumeText": resumeText,
                    "documentVector": documentVector,
                    "collectionVector": collectionVector})
                count_res += 1
                print(f"completed {count_res}")
            except Exception as e:
                # print(f"Error with: {res_name}: {e}")
                files.append({
                    "companyId": companyId,
                    "jobId": jobId,
                    "resumeName": None,
                    "resumeData": resumeData,
                    "resumeText": None,
                    "documentVector": None,
                    "collectionVector": collectionVector})
        except Exception as e:
            print(f"Error with: {result['_id']}: {e}")
            pass
    # print(len(files))
    result_collection_final.insert_many(files)

def update_candidate(ids):
    data = []
    for val in ids:
        # print(val)
        result = result_collection.find_one({"_id": ObjectId(str(val))})
        # print(result)
        jobId = result['jobId']
        companyId = result['companyId']
        resumeData = result['resumeData']
        collectionVector = model.encode(dict_to_string(result).strip()).tolist()

        try:
            resumeName = result['resumeData']['resumeName']
            resumeText, documentVector = download_and_process_resume(resumeName)
            data.append({
                "companyId": companyId,
                "jobId": jobId,
                "resumeName": resumeName,
                "resumeData": resumeData,
                "resumeText": resumeText,
                "documentVector": documentVector,
                "collectionVector": collectionVector})
        except Exception as e:
            data.append({
                "companyId": companyId,
                "jobId": jobId,
                "resumeName": None,
                "resumeData": resumeData,
                "resumeText": None,
                "documentVector": None,
                "collectionVector": collectionVector})
    print(data)
    result_collection_final.insert_many(data)
    delete_pdf()
        # print(f"Processing {resumeName}")



# update_existing()
# create_final_vecs()
# update_candidate(["651f82b23f1252001c7d93de"])