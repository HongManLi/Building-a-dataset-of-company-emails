import os

from dotenv import load_dotenv  # @UnresolvedImport

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
EMAIL_KEY = os.getenv('EMAIL_KEY')
NZBN_KEY = os.getenv('NZBN_KEY')
