# mongoDB PDF Vector Seeach

## Introduction

To begin, the text from the PDFs are extracted, split into sentences, and mapped into a 384 dimensional dense vector space. The PDF sentences along with their vectors are stored into MongoDB Atlas.
An Atlas Vector Search index then allows the PDFs to be queried, finding the PDFs that are relevant to the query. 

## Setup
### PDFs to Query
For this demo, the text extractor reads the PDFs from a local directory.

### Atlas
Open [params.py](params.py) and configure your connection to Atlas, along with the name of the database and collection you'd like to store your text. 

### Extract and Encode the PDFs
Install the requirements. This implementation uses:
* [PyPDF2](https://github.com/py-pdf/PyPDF2)    Python library for text extraction
* Hugging Face [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) pretrained model for the dense vector mapping
* [pymongo](https://pypi.org/project/pymongo/) - the Python driver for MongoDB

```zsh
pip install -r requirements.txt
```

Run the [extract_and_encode_pdf.py](extract_and_encode_pdf.py)

```python
python3 extract_and_encode.py
```

### Create Search Index
Create a default search index on the collection:
```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "sentenceVector": {
        "type": "knnVector",
        "dimensions": 384,
        "similarity": "euclidean" //can be changed
      }
    }
  }
}
```

## Demo

Your query will be mapped using the same sentence transformer that was used to encode the data and then submitted to Atlas Search, returning the top 3 matches.

For example:

```zsh
✗ python3 find_pdf.py -q "Data Scientist resume?"

The following PDFs may contain the answers you seek:
----------------------------------------------------
PDF:      Resume1.pdf

PDF:      Resume2.pdf

PDF:      Resume3.pdf
```

## The Search Query
This is the simple query passed to MongoDB:

```json
[
    {
        "$search": {
            "knnBeta": {
                "vector": <geneated query vector>,
                "path": "sentenceVector",
                "k": 150  // Number of neareast neighbors (nn) to return 
            }
        }
    },
    {
        "$limit": 3      
    }
]
```
