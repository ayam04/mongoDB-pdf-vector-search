# mongoDB PDF Vector Seeach

## Introduction

To begin, the text from the PDFs are extracted, split into sentences, and mapped into a 384 dimensional dense vector space. The PDF sentences along with their vectors are stored into MongoDB Atlas.
An Atlas Vector Search index then allows the PDFs to be queried, finding the PDFs that are relevant to the query. 

## Setup
the text extractor reads the PDFs from a local directory.

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

Run the [upload_files.py](upload_files.py)

```python
python3 upload_files.py
```

### Create Search Index
Create a default search index on the collection:
```json
{
  "fields": [
    {
      "numDimensions": 384,
      "path": "documentVector",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```

## Demo

Your query will be mapped using the same sentence transformer that was used to encode the data and then submitted to Atlas Search, returning the top 3 matches.

For example:

```zsh

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
    "$vectorSearch": {
      "index": "vector_index", 
      "path": "documentVector", 
      "queryVector": query_vector,
      "numCandidates": 150, 
      "limit": 3
    }
   }
]
```
