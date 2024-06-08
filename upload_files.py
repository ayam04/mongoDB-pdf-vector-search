from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import params
import os
from pymongo import MongoClient
from functions import *
import certifi
import time

mongo_client = MongoClient(params.mongodb_conn_string, tlsCAFile=certifi.where())
result_collection = mongo_client[params.database][params.collection]

files = []
pdfDir = "Resumes"

def encode_new_pdfs(pdfDir, job_description):
    start = time.time()
    for pdf_filename in os.listdir(pdfDir):
        try:
          pdf_path = os.path.join(pdfDir, pdf_filename)
          try:
              reader = PdfReader(pdf_path)
          except FileNotFoundError:
              print(f"File not found: {pdf_path}")
              continue
          number_of_pages = len(reader.pages)

          model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # Encoding model

          print(f"Encoding new PDF: {pdf_path}")

          pdf_text = ""
          for page_number in range(number_of_pages):
              page = reader.pages[page_number]
              pdf_text += page.extract_text()

          resume_text = clean_text(pdf_text)
          extracted_info = extract_info_from_resume(resume_text)
          processed_info = replace_na_and_empty_with_none(extracted_info)
          score = score_resume(job_description, resume_text)
          processed_info['jdMatchScore'] = score
          processed_info['resumeName'] = os.path.basename(pdf_path)
          print(processed_info)

          document_vector = model.encode(resume_text).tolist()

          result_doc = {
              "resumeData": processed_info,
              "documentVector": document_vector
          }
          files.append(result_doc)
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")
            continue
    if files:
        result_collection.insert_many(files)
    stop = time.time()
    print(stop - start)
    return "updated database"

with open("jd.txt", "r") as file:
    jd = file.read()

encode_new_pdfs(pdfDir, jd)
