from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util
import params
import os
from pymongo import MongoClient
from utils import split_into_sentences
import re


mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

result_collection.delete_many({})

files = []
pdfDir = "Resumes"

for pdf in os.listdir(pdfDir):
  print("Reading:", pdf)
  reader = PdfReader(os.path.join(pdfDir, pdf))
  number_of_pages = len(reader.pages)

  model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # Encoding model

  print("Encoding entire document...")

  pdf_text = ""
  for page_number in range(number_of_pages):
    page = reader.pages[page_number]
    pdf_text += page.extract_text()

  document_vector = model.encode(pdf_text).tolist()

  result_doc = {
      "pdf": pdf,
      "pdf_text": pdf_text,
      "documentVector": document_vector
  }

  result = result_collection.insert_one(result_doc.copy())
