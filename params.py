import urllib.parse as prs

password = "<password>"
username = "<username>"
mongodb_conn_string = f"mongodb+srv://{username}:{prs.quote_plus(password)}@cluster0.hdcpwsw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&ssl=true"
database = "test1"
collection = "resumes"