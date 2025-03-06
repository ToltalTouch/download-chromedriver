import requests
import wget
import zipfile
import os

url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
response = requests.get(url, verify=False)
version_number = response.text.strip()

download_url = f"https://chromedriver.storage.googleapis.com/{version_number}/chromedriver_win32.zip"

latest_driver_zip = wget.download(download_url, 'chromedriver.zip')

with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
    zip_ref.extractall()
os.remove(latest_driver_zip)