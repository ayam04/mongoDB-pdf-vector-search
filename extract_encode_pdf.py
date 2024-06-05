from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util
import params
import os
from pymongo import MongoClient
from utils import *
import re


mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

result_collection.delete_many({})

files = []
pdfDir = "Resumes"

for pdf in os.listdir(pdfDir):

    print("Reading:", pdf)
    reader = PdfReader(pdfDir+"/"+pdf)
    number_of_pages = len(reader.pages)

#   https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2') //encoding model

    print("Encoding", number_of_pages, "pages...")

    for page_number in range(number_of_pages):
        print(page_number+1)

        page = reader.pages[page_number]

        text = page.extract_text()
        sentences = split_into_sentences(text)

        result_doc = {}

        for sentence in sentences:
            if (not re.search("^[a-zA-Z]\s[a-zA-Z]\s", sentence)):

                sentence_vector = model.encode(sentence).tolist()
                result_doc['pdf'] = pdf
                result_doc['page'] = page_number
                result_doc['sentence'] = sentence
                result_doc['sentenceVector'] = sentence_vector
                result = result_collection.insert_one(result_doc.copy())
