import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN_TELEGRAM")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
GOOGLE_CREDENTIALS_FILE = "key.json"