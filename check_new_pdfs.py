from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import params
import os
from pymongo import MongoClient
from functions import *
import certifi


def encode_new_pdf(pdf_path, job_description):

  mongo_client = MongoClient(params.mongodb_conn_string, tlsCAFile=certifi.where())
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
      "resumeData": processed_info,
      "documentVector": document_vector
  }

  result_collection.insert_one(result_doc.copy())

pdfDir = "Resumes"
with open("jd.txt", "r") as file:
  jd = file.read()

# encode_new_pdf("Resumes/Resume 1.pdf", jd)
score = score_resume(jd, """0
"Domestic & international travel expertise"
"Budgeting & accounting"
"Logistical planning"
"Itineraries"
"Reservations"
"Travel Consulting"
"Russian"
"French
             
             Tasked with making arrangements for tours, including, but not limited to, tourist attractions, transport, accommodation, and car rentals for the African continent focusing on responsible and sustainable accommodation establishments and also destination weddings. Provided advice about destinations and packages to tourists. Provided recommendations about tour and vacation packages provided by the company. Visited hotels and restaurants to improve accuracy on the travel agency's information such as cleanliness and available facilities so that recommendations are accurate. Handle bookings, invoices and issue tickets as well as confirm customers' names with airlines/hotels. Provide pricing information, brochures, and internet-based information.
             Primary responsibility to coordinate with local Tourist Guides to create itineraries for their clients according to specific guidelines and preferences also to handle all post-sales documents, pre-paid inventory management, rail booking, and document shipping. Attended client’s queries on the phone, via the Internet, and in person. Provided suggestions about how the company website can be improved for ease of use, completeness, and marketability, if and when necessary. Checked the weather conditions and forecasts; coordinated with local government bodies about the nature of the trips, and encased emergencies.""")

print(score)