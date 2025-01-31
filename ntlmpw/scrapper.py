import requests
import urllib3
from bs4 import BeautifulSoup
import math
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {
    "http": "socks5h://YOURSOCKSPROXY",
    "https": "socks5h://YOURSOCKSPROXY"
}

headers = {
    'Host': 'ntlm.pw',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Origin': 'https://ntlm.pw',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://ntlm.pw/',
    'Priority': 'u=0, i',
    'Connection': 'keep-alive',
}

def read_hashes(file_path):
    try:
        with open(file_path, 'r') as file:
            hashes = [line.strip() for line in file if line.strip()]
        return hashes
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{file_path}' n'a pas été trouvé.")
        sys.exit(1)
    except Exception as e:
        print(f"Une erreur s'est produite lors de la lecture du fichier : {e}")
        sys.exit(1)

def chunk_hashes(hashes, chunk_size=399):
    for i in range(0, len(hashes), chunk_size):
        yield hashes[i:i + chunk_size]

def send_request(session, url, headers, proxies, hashes_chunk, hashtype='nt'):
    hashes_str = '\r\n'.join(hashes_chunk)
    data = {
        'hashes': hashes_str,
        'hashtype': hashtype,
    }
    try:
        response = session.post(url, headers=headers, data=data, proxies=proxies, verify=False, timeout=30)
        return response
    except requests.exceptions.ProxyError as e:
        print(f"Erreur de proxy : {e}")
        return None
    except requests.exceptions.ConnectTimeout:
        print("Erreur : Délai de connexion dépassé.")
        return None
    except requests.exceptions.ReadTimeout:
        print("Erreur : Délai de lecture dépassé.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        return None

def parse_response(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tbody = soup.find('tbody')
    if not tbody:
        print("Aucun <tbody> trouvé dans la réponse HTML.")
        return []
    
    rows = tbody.find_all('tr')
    results = []
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            hash_cell = cols[0].find('h6')
            hash_text = hash_cell.get_text(strip=True) if hash_cell else ''
            
            password_cell = cols[1].find('h6')
            password_text = password_cell.get_text(strip=True) if password_cell else ''
            
            if password_text.lower() != '[not found]':
                results.append(f"{hash_text}:{password_text}")
    
    return results

def main():
    input_file = 'input_hashes.txt'
    output_file = 'hashes_passwords.txt'
    url = 'https://ntlm.pw/'
    
    hashes = read_hashes(input_file)
    total_hashes = len(hashes)
    print(f"Nombre total de hashes à traiter : {total_hashes}")
    
    if total_hashes == 0:
        print("Aucun hash à traiter.")
        sys.exit(0)
    
    chunks = list(chunk_hashes(hashes, 399))
    total_chunks = len(chunks)
    print(f"Nombre total de requêtes à envoyer : {total_chunks}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            with requests.Session() as session:
                for idx, chunk in enumerate(chunks, 1):
                    print(f"Envoi de la requête {idx}/{total_chunks} avec {len(chunk)} hashes...")
                    response = send_request(session, url, headers, proxies, chunk, hashtype='nt')
                    
                    if response and response.status_code == 200:
                        print(f"Réponse reçue pour la requête {idx}/{total_chunks} (Statut : {response.status_code})")
                        parsed_results = parse_response(response.text)
                        
                        if parsed_results:
                            for line in parsed_results:
                                outfile.write(line + '\n')
                            print(f"{len(parsed_results)} paires hash:motdepasse extraites.")
                        else:
                            print("Aucune paire valide trouvée dans cette réponse.")
                    else:
                        if response:
                            print(f"Erreur : Statut de la réponse : {response.status_code}")
                        else:
                            print(f"Erreur : La requête {idx} a échoué.")
                    

                    
        print(f"\nProcessus terminé. Les résultats ont été enregistrés dans '{output_file}'.")
    except IOError as e:
        print(f"Erreur lors de l'ouverture du fichier de sortie : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
