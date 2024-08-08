import os
import time
import shutil
import params
import boto3
import certifi
from functions import *
from docx import Document
from PyPDF2 import PdfReader
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from bson import ObjectId

load_dotenv()

mongodb_conn_string = os.getenv("mongodb_conn_string")
database = os.getenv("database")
collection = os.getenv("collection")
collection_vec = os.getenv("collection_vec")
collection_final = os.getenv("collection_final")

mongo_client = MongoClient(mongodb_conn_string, tlsCAFile=certifi.where())
result_collection = mongo_client[database][collection]
result_collection_vec = mongo_client[database][collection_vec]
result_collection_final = mongo_client[database][collection_final]

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')
bucket_name = 'hyrgpt-stage-s3'
s3_path = 'resumes'

s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # Encoding model

files = []
pdfDir = "Resumes"

def get_company_id():
    unique_company_ids = result_collection.distinct("companyId")
    unique_company_ids_str = [str(company_id) for company_id in unique_company_ids]
    print(len(unique_company_ids_str))
    return unique_company_ids_str

def get_resumes(companyId):
    resId = []

    query = {"companyId": ObjectId(companyId),"resumeData.resumeName": {"$ne": "", "$exists": True}}

    documents = result_collection.find(query)
    for document in documents:
        try:
            resId.append(document['resumeData']['resumeName'])
        except Exception as e:
            print(f"Error with: {document['_id']}: {e}")
            continue
    return resId

def download_resumes(resumes):
    for resume in resumes:
        try:
            objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{s3_path}/{resume}")
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    key = obj['Key']
                    if ((not key.endswith('/')) and key.endswith('.pdf')):
                        file_name = os.path.basename(key)
                        local_file_path = os.path.join("Resumes", file_name)

                        with open(local_file_path, 'wb') as f:
                            s3.download_fileobj(bucket_name, key, f)

                print('Download completed!')
            else:
                print('No files found in the specified S3 path.')
        except Exception as e:
            print(f"Error with: {resume}: {e}")
            continue

# def download_all_resumes():
#     continuation_token = None
#     try:
#         while True:
#             if continuation_token:
#                 objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_path, ContinuationToken=continuation_token)
#             else:
#                 objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_path)
            
#             # print(objects)
#             print(len(objects["Contents"]))

#             # if 'Contents' in objects:
#             #     for obj in objects['Contents']:
#             #         key = obj['Key']
#             #         if key.endswith('.pdf'):
#             #             file_name = os.path.basename(key)
#             #             local_file_path = os.path.join("Resumes", file_name)

#             #             with open(local_file_path, 'wb') as f:
#             #                 s3.download_fileobj(bucket_name, key, f)

#             #     print('Download completed for this page!')

#             if objects.get('IsTruncated'):  # Check if there are more pages
#                 continuation_token = objects['NextContinuationToken']
#             else:
#                 break  # Exit the loop if no more pages are left

    # except Exception as e:
    #     print(f"Error: {e}")

def get_resume_text_and_upload(companyId):
    resumes = get_resumes(companyId)
    download_resumes(resumes)
    for resume in resumes:
        try:
            pdf_path = os.path.join("Resumes", resume)
            try:
                reader = PdfReader(pdf_path)
            except FileNotFoundError:
                print(f"File not found: {pdf_path}")
                continue
            number_of_pages = len(reader.pages)

            print(f"Encoding new PDF: {pdf_path}")

            pdf_text = ""
            for page_number in range(number_of_pages):
                page = reader.pages[page_number]
                pdf_text += page.extract_text()

            resume_text = clean_text(pdf_text)
            resume_text = replace_na_and_empty_with_none(resume_text)
            # print(resume_text)
            document_vector = model.encode(resume_text).tolist()

            result_doc = {
                "companyId": ObjectId(companyId),
                "resumeName": resume,
                "documentVector": document_vector
            }
            files.append(result_doc)
        except Exception as e:
            print(f"Error with: {resume}: {e}")
            continue
    if files:
        try:
            result_collection_vec.insert_many(files)
        except Exception as e:
            print(f"Error with uploading: {e}")
    delete_pdf()

def delete_pdf():
    folder = "Test"
    shutil.rmtree(folder); os.makedirs(folder)

def update_for_company():
    company_ids = get_company_id()
    for company_id in company_ids:
        get_resume_text_and_upload(company_id)

def encode_new_pdfs(pdfDir="Resumes", job_description=None):
    files = []
    start = time.time()
    for pdf_filename in os.listdir(pdfDir):
        try:
          companyId = get_company_for_resume(pdf_filename)
          if companyId is None:
              print(f"no company for: {pdf_filename}")
              continue
          else:
            pdf_path = os.path.join(pdfDir, pdf_filename)
            try:
                reader = PdfReader(pdf_path)
            except FileNotFoundError:
                print(f"File not found: {pdf_path}")
                continue
            number_of_pages = len(reader.pages)


            print(f"Encoding new PDF: {pdf_path}")

            pdf_text = ""
            for page_number in range(number_of_pages):
                page = reader.pages[page_number]
                pdf_text += page.extract_text()

            resume_text = clean_text(pdf_text)
            #   extracted_info = extract_info_from_resume(resume_text)
            processed_info = replace_na_and_empty_with_none(resume_text)
            #   score = score_resume(job_description, resume_text)
            #   processed_info['jdMatchScore'] = score
            #   processed_info['resumeName'] = os.path.basename(pdf_path)
            #   print(processed_info)
            document_vector = model.encode(processed_info).tolist()

            result_doc = {
                    "companyId": ObjectId(companyId),
                    "resumeName": pdf_filename,
                    "documentVector": document_vector
            }
            files.append(result_doc)
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")
            continue
    result_collection_vec.insert_many(files)
    stop = time.time()
    print(stop - start)
    return "updated database"

with open("jd.txt", "r") as file:
    jd = file.read()

def get_company_for_resume(resume_name):
    document = result_collection.find_one({"resumeData.resumeName": resume_name})
    if document is None:
        return None
    elif "companyId" not in document:
        return None
    else:
        return document["companyId"]

# encode_new_pdfs(pdfDir, None)

def s3_everything():
    files = []
    company_ids = get_company_id()
    count = 0
    # print(len(company_ids))
    for company_id in company_ids:
        resumes = get_resumes(company_id)
        # print(company_id, len(resumes))
        for resume in resumes:
            try:
                key = f"{s3_path}/{resume}"
                if key.endswith('.pdf'):
                    with open(f"Test/{resume}", 'wb') as file:
                        s3.download_fileobj(bucket_name,key,file)
            except Exception as e:
                print(f"Error download: {resume}: {e}")
                continue
        for resume in resumes:
            try:
                try:
                    pdf_path = f"Test/{resume}"
                    try:
                        reader = PdfReader(pdf_path)
                    except FileNotFoundError:
                        print(f"File not found: {pdf_path}")
                        continue
                    number_of_pages = len(reader.pages)

                    print(f"Encoding new PDF: {pdf_path}")

                    pdf_text = ""
                    for page_number in range(number_of_pages):
                        page = reader.pages[page_number]
                        pdf_text += page.extract_text()

                    resume_text = clean_text(pdf_text)
                    resume_text = replace_na_and_empty_with_none(resume_text)
                    # print(resume_text)
                    document_vector = model.encode(resume_text).tolist()

                    result_doc = {
                        "companyId": ObjectId(company_id),
                        "resumeName": resume,
                        "resumeText": resume_text,
                        "documentVector": document_vector
                    }
                    files.append(result_doc)
                    count+=1
                    print(count)
                except Exception as e:
                    print(f"some error: {resume}: {e}")
                    continue
            except Exception as e:
                print(f"Error with: {resume}: {e}")
                continue
    result_collection_vec.insert_many(files)

def download_and_process_resume(resumeName):
    key = f"{s3_path}/{resumeName}"
    try:
        if key.endswith('.pdf'):
            with open(f"Test/{resumeName}", 'wb') as file:
                s3.download_fileobj(bucket_name,key,file)
            reader = PdfReader(key)
            number_of_pages = len(reader.pages)
            pdf_text = ""
            for page_number in range(number_of_pages):
                page = reader.pages[page_number]
                pdf_text += page.extract_text()
            resume_text = clean_text(pdf_text)
            resume_text = replace_na_and_empty_with_none(resume_text)
            documentVector = model.encode(resume_text).tolist()
        
        elif key.endswith('.docx'):
            with open(f"Test/{resumeName}", 'wb') as file:
                s3.download_fileobj(bucket_name,key,file)
            doc = Document(key)
            resume_text = "\n".join([para.text for para in doc.paragraphs])
            resume_text = clean_text(resume_text)
            resume_text = replace_na_and_empty_with_none(resume_text)
            documentVector = model.encode(resume_text).tolist()

        return(resume_text, documentVector)

        
    except Exception as e:
        print(f"Error download: {resumeName}: {e}")

# print(get_company_id())
# print(get_resumes("651f80883f1252001c7d9379"))
# download_resumes(['455082532462504_896773346629580_test.pdf', '460351885733437_896773346629580_test.pdf'])
# get_resume_text_and_upload("651f80883f1252001c7d9379")
# update_for_company()
# download_all_resumes()
# delete_pdf()
# print(get_company_for_resume("000047541731056_Alaa_Jaafar_5458606.pdf"))
# s3_everything()
