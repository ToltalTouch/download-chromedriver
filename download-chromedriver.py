import requests
import wget
import logging
import winreg
import zipfile
import os
import urllib3
import ssl
from tqdm import tqdm

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure requests to use a more permissive SSL configuration if needed
try:
    # Create a custom SSL context that's more permissive
    custom_context = ssl.create_default_context()
    custom_context.check_hostname = False
    custom_context.verify_mode = ssl.CERT_NONE
    
    # Try to improve SSL compatibility
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
except (AttributeError, ImportError):
    pass  # Older versions might not support this

atual_dir = os.path.dirname(os.path.abspath(__file__))

def download_chromedriver(url, destination):
    """Download ChromeDriver with retry logic and fallback methods"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logging.info(f"Tentativa {retry_count + 1} de {max_retries} para baixar ChromeDriver")
            # Try standard requests download
            response = requests.get(url, stream=True, verify=False, timeout=30)
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))

            with open(destination, 'wb') as f, tqdm(
                desc=f"Baixando",
                total=total,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    bar.update(len(data))
            
            # If we get here, download was successful
            logging.info("Download concluído com sucesso usando requests")
            return True
        
        except (requests.exceptions.RequestException, requests.exceptions.SSLError) as e:
            retry_count += 1
            logging.warning(f"Erro ao baixar usando requests: {e}")
            if retry_count < max_retries:
                logging.info(f"Tentando novamente em 3 segundos...")
                import time
                time.sleep(3)
            else:
                logging.info("Falha no download com requests, tentando método alternativo com wget...")
                try:
                    # Try wget as a fallback
                    wget.download(url, destination)
                    print()  # Add newline after wget output
                    logging.info("Download concluído com sucesso usando wget")
                    return True
                except Exception as wget_error:
                    logging.error(f"Falha no método alternativo de download: {wget_error}")
                    return False

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def find_chrome_path_from_registry(): # Funcao para entrar nos registros do windows(regedit) e encontrar a versao do chrome instaldo
    try:
        register_path = {
            r"SOFTWARE\Google\Chrome\BLBeacon",  # Instalação para todos os usuários
            r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon",  # Para versões 64 bits            
        }

        for register in register_path: # Loop de pesquis, caso não seja a primeira opção da lista, então procura a segunda
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, register) # Identificando que o caminho é o do usuário atual
                version, _= winreg.QueryValueEx(key, "version") # Obtendo a versão do Chrome
                logging.info(f"Versão do Chrome encontrada: {version}")
                return version
            except FileNotFoundError:
                logging.info(f"Chave de registro não encontrada: {register}")
    except Exception as e:
        logging.error(f"Erro ao acessar o registro do Windows: {e}")

def search_chromedriver(version_chrome):
    major_version = version_chrome.split('.')[0] # Encontra a primeria parte do codigo de versao do chrome, exemplo: 123.333.666 == "123"
    url_json = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    response = requests.get(url_json) # Requisitando o JSON que contem as versõe do Chrome e seus drivers
    response.raise_for_status() # Verifica se a requisição foi bem sucedida
    date = response.json() # Carrega o JSON em um dicionário

    for version in reversed(date["versions"]): # Loop para verificar todas as versões ate encontrar a correta
        if version["version"].startswith(major_version):
            for item in version["downloads"]["chromedriver"]:
                if item["platform"] == "win64":
                    return version["version"], item["url"]
    return None, None

def main():
    version_chrome = find_chrome_path_from_registry() # Chama a função que encontra a versão do Chrome
    if not version_chrome:
        logging.info("Não foi possiver detectar a versão do Chrome instalada.")
        return
    logging.info(f"Versão do Chrome encontrada")

    version_driver, url_download = search_chromedriver(version_chrome) # Chama a função que procura o ChromeDriver compatível com a versão do Chrome
    if not version_driver:
        logging.info("Não foi possível encontrar o ChromeDriver compatível.")
        return    logging.info(f"Versão do ChromeDriver encontrada: {version_driver}")
    logging.info(f"URL de download do ChromeDriver: {url_download}")
    
    path_zip = os.path.join(atual_dir, "chromedriver.zip") # Define o caminho de saída para o arquivo zip do ChromeDriver
    os.makedirs(atual_dir, exist_ok=True) # Cria o diretório atual se não existir

    # Tenta o download com tratamento de falhas
    download_success = download_chromedriver(url_download, path_zip)
    
    if not download_success:
        # Se falhar, tenta um método alternativo usando a URL legacy
        major_version = version_chrome.split('.')[0]
        legacy_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        
        try:
            logging.info(f"Tentando método alternativo com URL legacy: {legacy_url}")
            response = requests.get(legacy_url, verify=False, timeout=30)
            driver_version = response.text.strip()
            alt_download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
            logging.info(f"URL alternativa encontrada: {alt_download_url}")
            
            download_success = download_chromedriver(alt_download_url, path_zip)
        except Exception as e:
            logging.error(f"Erro no método alternativo: {e}")
            return
    
    if not download_success:
        logging.error("Todas as tentativas de download falharam. Encerrando.")
        return
    
    try:
        # Extrai o arquivo apenas se o download for bem-sucedido
        extract_zip(path_zip, atual_dir)
        os.remove(path_zip) # Remove o arquivo zip após a extração
    except Exception as e:
        logging.error(f"Erro ao extrair arquivo: {e}")
        return

    # Verifica ambos os possíveis nomes de diretório (chromedriver-win64 ou chromedrive-win64)
    path_driver = os.path.join(atual_dir, "chromedriver-win64", "chromedriver.exe") # Define o caminho do ChromeDriver extraído
    if not os.path.exists(path_driver):
        path_driver = os.path.join(atual_dir, "chromedrive-win64", "chromedriver.exe") # Caminho alternativo (typo)
    if os.path.exists(path_driver):
        logging.info(f"ChromeDriver baixado com sucesso: {path_driver}")
    else:
        logging.error("Erro ao baixar o ChromeDriver.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()