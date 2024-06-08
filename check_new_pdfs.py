from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import params
import os
from pymongo import MongoClient
from functions import *


def encode_new_pdf(pdf_path, job_description):

  mongo_client = MongoClient(params.mongodb_conn_string)
  result_collection = mongo_client[params.database][params.collection]
  reader = PdfReader(pdf_path)
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
  score = score_resume(job_description,resume_text)
  processed_info['jdMatchScore'] = score
  processed_info['resumeName'] = os.path.basename(pdf_path)
  print(processed_info)

  document_vector = model.encode(resume_text).tolist()

  result_doc = {
      "resumeData": pdf_text,
      "documentVector": document_vector
  }

  result_collection.insert_one(result_doc.copy())

pdfDir = "Resumes"
with open("jd.txt", "r") as file:
  jd = file.read()

encode_new_pdf("Resumes/Resume 1.pdf", jd)