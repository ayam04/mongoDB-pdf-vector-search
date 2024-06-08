import re
import json
import openai
from colorama import Fore, Style

# scoring
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import os
from dotenv import load_dotenv

# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()


load_dotenv()
openai.api_key = os.getenv("API_KEY")

def clean_text(text):
    """
    Extracts text content from a resume file.

    Parameters:
        file (file): The resume file object.

    Returns:
        str: The extracted text content from the resume.
    """
    try:
        text = text.replace("\\", "/")
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)

        if text[0] == '\n':
            text = text[1:]

        if len(text) >= 5000:
            text = text[:5000]

        return text
    except Exception as err:
        print(f"{Fore.RED}ERROR in extract_text Function: {err}{Style.RESET_ALL}")

def clean_phone(pno):
    if isinstance(pno, list):
        pno = pno[0]
    seperator_list = [',','/']
    for sep in seperator_list:
        if sep in pno:
            pno = pno.split(sep)[0]
    chars = '1234567890'
    for i in pno:
        if i not in chars:
            pno = pno.replace(i,'')
    return pno

def extract_info_from_resume(resume_text):
    """
    Extracts important information from the resume text using OpenAI Chat API.

    Parameters:
        resume_text (str): The text content of the resume.

    Returns:
        str: A JSON string containing the extracted information in a specific format.
    """
    query = """
    The JSON should be in this format:
    {
        "name": "",
        "email": "",
        "phoneNumber":
        "linkedin": "" (only fill out this field if a link is present in the text in the form of "https://www.linkedin.com/in/"),
        "education": {
            "undergraduate": {
                "degree": "",
                "graduationDate": "",
                "gpa": "",
                "collegeName": "",
                "minor": ""
            },
            "graduate": {}
        },
        "jobHistory": [
            {
                "companyName": "",
                "position": "",
                "startDate": "",
                "endDate": "",
                "description": ""
            },
            {
                "companyName": "",
                "position": "",
                "startDate": "",
                "endDate": "",
                "description": ""
            }
        ],
        "projects": [
            {
                "projectName": "",
                "startDate": "",
                "endDate": "",
                "description": ""
            }
        ],
        "skills": [] (skills should be verbatim from the text, do not make any modifications when appending to array)
    }

    Important Rules To Follow When Creating JSON as well:
      - No Other Keys Should Exist in the JSON other than the one presented in the template
      - If a certain field does not exist just leave it as "N/A".
      - If there are multiple phone numbers present, keep them comma  ',' seperated.
      - If First Name and Last Name are combined together, leave it as is, don't add any spaces
      - Add a LinkedIn value to the key "linkedin" only if it is explicitly mentioned in the form of a link starting with "https://www.linkedin.com/in/" followed by unique text, without making any assumptions.
      - When adding values to any of the keys in the JSON, copy and paste exactly as worded on the resume. Under no circumstances make any changes to the original text when setting a value.
      - For the "jobHistory" key, any experience is considered valid data.
      - For the "description" key under "jobHistory", remove all new lines and extra spaces.
    """

    prompt = f"Extract important information from the resume text: {resume_text} in a return type of JSON:```\n{query}\n---\n```\n\n\n DO NOT GO OUT OF CONTEXT. ONLY PROVIDE DETAILS EXTRACTED FROM THE RESUME. ONLY OUTPUT AS JSON."
    count = 0
    while count < 1:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0
            )
            info = response['choices'][0]['message']['content'].strip("\n").strip()
            info = json.loads(info)
            info['phoneNumber'] = clean_phone(info['phoneNumber'])
            return info
        except Exception as err:
            print(f"{Fore.RED}ERROR in extract_info_from_resume Function: {err}{Style.RESET_ALL}")
            count+=1
            


def replace_na_and_empty_with_none(data):
    """
    Replaces "N/A" and empty values with None in a dictionary or list.

    Parameters:
        data (dict or list): The dictionary or list to process.

    Returns:
        dict or list: The processed dictionary or list with "N/A" and empty values replaced by None.
    """
    try:
        if isinstance(data, dict):
            return {
                key: replace_na_and_empty_with_none(value)
                if value != "N/A" and value != ""
                else None
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [replace_na_and_empty_with_none(item) if item != "N/A" and item != "" else None for item in data]
        else:
            return data
    except Exception as err:
        print(f"{Fore.RED}ERROR in replace_na_and_empty_with_none Function: {err}{Style.RESET_ALL}")


def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return 'a'  # Adjective
    elif treebank_tag.startswith('V'):
        return 'v'  # Verb
    elif treebank_tag.startswith('N'):
        return 'n'  # Noun
    elif treebank_tag.startswith('R'):
        return 'r'  # Adverb
    else:
        return 'n'  # Default to noun

def preprocess_text(text):
    tokens = word_tokenize(text)
    filtered_tokens = [lemmatizer.lemmatize(word.lower(), get_wordnet_pos(pos)) for word, pos in pos_tag(tokens) if word.lower() not in stop_words]
    out = ' '.join(filtered_tokens)
    return out


def score_resume(job_description, resume_text):
    vectorizer = TfidfVectorizer()
    vec_data = [preprocess_text(job_description), preprocess_text(resume_text)]
    vecs = vectorizer.fit_transform(vec_data).toarray()
    similarity = cosine_similarity(vecs[0].reshape(1, -1), vecs[1].reshape(1, -1))[0][0]
                                
    return float("{:.2f}".format(similarity*100))


# def score_scaler(x):
#   x = float(x)
#   mul = -0.1721*(x)/5 + 3.2967
#   y = min(x*max(1.6,mul),85)
#   return float("{:.2f}".format(y))


# def get_resp_jd(jd):
#     format_json = '''{"text": <body of text>, "domain": <Domain the JD describes>,"entities": [{"Entity": Type (responsibility, requirement, qualification), "text": <text>, "start": starting index, "end": ending index }, .....]}'''
#     prompt = f'''
#     You are an expert Data labeler for Job descriptions. You will be given text from job descriptions, You need to tag the responsibilities/roles , Requirements and qualifications section out of the same in the following json format:
#     {format_json}
#     Job Description: {jd}

#     Important things while creating the json:
#     1. NO other field except the ones described.
#     2. ONLY give the JSON as an output, no other text explaining.
#     3. Get ALL the roles/responsibilities and qualification lines even if you have lower confidence.
#     '''
#     response = openai.ChatCompletion.create(
#                 model="gpt-3.5-turbo-1106",
#                 messages=[
#                     {"role": "user", "content": prompt},
#                 ],
#                 temperature=0
#             )
#     response = response['choices'][0]['message']['content'].strip("\n").strip()

    
#     response = json.loads(response)
#     jd_short = ''

#     for resp in response['entities']:
#         jd_short += resp['text'] + '\n'
    
#     return jd_short