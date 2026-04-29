from dotenv import load_dotenv
import os
load_dotenv()
google = os.getenv('GOOGLE_API_KEY')
ncbi = os.getenv('NCBI_API_KEY')
print('Google API key loaded:', '✅' if google and google.startswith('AIza') else '❌')
print('NCBI key loaded:', '✅' if ncbi else '❌')