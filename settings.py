from dotenv import load_dotenv
load_dotenv()
import os
PASSWORD = os.getenv("PASSWORD")
USER=os.getenv("USER")
HOST=os.getenv("HOST") 
DB=os.getenv("DB")
