from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util
import params
import os
from pymongo import MongoClient
import time

pdfDir = "Resumes"

def encode_new_pdf(pdf_path):
  reader = PdfReader(pdf_path)
  number_of_pages = len(reader.pages)

  model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # Encoding model

  print(f"Encoding new PDF: {pdf_path}")

  pdf_text = ""
  for page_number in range(number_of_pages):
    page = reader.pages[page_number]
    pdf_text += page.extract_text()

  document_vector = model.encode(pdf_text).tolist()

  result_doc = {
      "pdf": os.path.basename(pdf_path),
      "pdf_text": pdf_text,
      "documentVector": document_vector
  }

  result_collection.insert_one(result_doc.copy())


mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

existing_filenames = set([f for f in os.listdir(pdfDir)])

while True:
  all_filenames = set(os.listdir(pdfDir))
  new_filenames = all_filenames - existing_filenames

  for filename in new_filenames:
    pdf_path = os.path.join(pdfDir, filename)
    encode_new_pdf(pdf_path)

  existing_filenames = all_filenames
  time.sleep(10) # can be ignored for constant checking

  print("Checking for new PDFs...")
