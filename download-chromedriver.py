import subprocess
import requests
import wget
import zipfile
import os
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_chrome_path():
    possible_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def get_chrome_version_from_exe(chrome_path):
    try:
        output = subprocess.check_output([chrome_path, '--version'], text=True)
        version = output.strip().replace("Google Chrome", "").strip()
        return version
    except Exception as e:
        print("Erro ao obter versão do Chrome:", e)
        return None

chrome_path = find_chrome_path()
if not chrome_path:
    print("Chrome não encontrado.")
    exit()

chrome_version = get_chrome_version_from_exe(chrome_path)
if not chrome_version:
    print("Não foi possível obter a versão do Chrome.")
    exit()

major_version = chrome_version.split('.')[0]

# Obter a versão do ChromeDriver compatível
metadata_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
response = requests.get(metadata_url, verify=False)
driver_version = response.text.strip()

# Baixar e extrair o driver
download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
latest_driver_zip = wget.download(download_url, 'chromedriver.zip')

print("\nExtraindo driver...")
with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
    zip_ref.extractall()

os.remove(latest_driver_zip)
print("Feito!")