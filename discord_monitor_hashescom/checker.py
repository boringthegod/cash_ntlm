import os
import requests
import subprocess
import re

API_FILE = "/root/hashescom/api.txt"
STORAGE_FILE = "/root/hashescom/ntlm_jobs.txt"
WEBHOOK_URL = "YOURDISCORDWEBHOOKURL"
NTLM_ALG_ID = "1000"

def format_and_upload_found_hashes(stdout_decoded, job_id, apikey):
    """
    - Parse le stdout d'un multiget_rocksdb (ou autre) contenant des lignes "[FOUND] ... => ..."
    - Reformate ces lignes au format "hash:plain"
    - Sauvegarde dans un fichier
    - Uploade vers l'API hashes.com
    """
    msg_found = f"Hash trouvé pour l'id {job_id}."
    data_found = {"content": msg_found}
    resp_found = requests.post(WEBHOOK_URL, data=data_found)
    if resp_found.status_code in [200, 204]:
        print("Message (truc trouvé) envoyé sur Discord avec succès.")
    else:
        print(f"Échec de l'envoi du message (code {resp_found.status_code}).")
    found_lines = []

    pattern = r'^\[FOUND\]\s+([0-9a-fA-F]+)\s+=>\s+(.*)$'
    
    for line in stdout_decoded.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            hash_part = match.group(1)
            pass_part = match.group(2)
            found_lines.append(f"{hash_part}:{pass_part}")

    if not found_lines:
        print(f"Aucun hash trouvé à uploader pour le job {job_id}.")
        return

    output_file_formatted = f"/tmp/{job_id}_formatted.txt"
    with open(output_file_formatted, "w") as f_out:
        for fl in found_lines:
            f_out.write(fl + "\n")

    print(f"Fichier reformatté écrit dans : {output_file_formatted}")

    upload_url = "https://hashes.com/en/api/founds"
    data = {
        "key": apikey,
        "algo": "1000"
    }
    files = {
        "userfile": open(output_file_formatted, "rb")
    }

    try:
        resp = requests.post(upload_url, data=data, files=files)
        resp_json = resp.json()
        if resp.status_code == 200 and resp_json.get("success", False):
            print(f"Upload réussi pour le job {job_id}.")
        else:
            print(f"Upload échoué pour le job {job_id}. Raison : {resp_json.get('message','Inconnue')}")
    except requests.RequestException as e:
        print(f"Erreur lors de l'upload du job {job_id} : {e}")

def main():
    if not os.path.exists(API_FILE):
        print(f"Le fichier {API_FILE} est introuvable. Veuillez y mettre votre clé d'API.")
        return
    with open(API_FILE, "r") as f:
        apikey = f.read().strip()
    if not apikey:
        print("Aucune clé d'API n'a été trouvée dans api.txt.")
        return

    known_ids = set()
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            for line in f:
                line_id = line.strip()
                if line_id:
                    known_ids.add(line_id)

    url = f"https://hashes.com/en/api/jobs?key={apikey}"

    try:
        response = requests.get(url).json()

        if not response.get("success"):
            print("Impossible de récupérer les jobs. Message d'erreur :", response.get("message", "N/A"))
            return

        jobs = response["list"]
        ntlm_jobs = [job for job in jobs if str(job["algorithmId"]) == NTLM_ALG_ID]

        ntlm_ids = set(str(job["id"]) for job in ntlm_jobs)

        new_ids = ntlm_ids - known_ids

        if new_ids:
            new_ids_sorted = sorted(new_ids)
            message = "Nouveaux jobs NTLM détectés : " + ", ".join(new_ids_sorted)

            data = {"content": message}
            resp = requests.post(WEBHOOK_URL, data=data)

            if resp.status_code in [200, 204]:
                print("Message (nouveaux jobs) envoyé sur Discord avec succès.")
            else:
                print(f"Échec de l'envoi du message (code {resp.status_code}).")

            for job in ntlm_jobs:
                job_id = str(job["id"])
                if job_id in new_ids:
                    left_list_url = "http://hashes.com" + job["leftList"]
                    print(f"Téléchargement de la liste pour le job {job_id}...")
                    try:
                        dl_resp = requests.get(left_list_url, stream=True)
                        dl_resp.raise_for_status()
                        
                        out_path = f"/tmp/{job_id}.txt"
                        with open(out_path, "wb") as outfile:
                            for chunk in dl_resp.iter_content(chunk_size=8192):
                                outfile.write(chunk)
                        print(f"Fichier téléchargé : {out_path}")

                        with open(out_path, "r") as f:
                            content = f.read()
                            print(f"Contenu de {out_path} :\n{content}")

                        cmd = ["/root/rocksdb/multiget_rocksdb", "/root/rocksdb/my_rocksdb", out_path]
                        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = process.communicate()
                        stdout_decoded = stdout.decode("utf-8", errors="replace").strip()

                        if stdout_decoded:
                            format_and_upload_found_hashes(stdout_decoded, job_id, apikey)
                        else:
                            print(f"Aucun résultat pour le job {job_id}.")

               

                    except requests.RequestException as e:
                        print(f"Erreur lors du téléchargement pour le job {job_id}: {e}")

            with open(STORAGE_FILE, "a") as f:
                for job_id in new_ids_sorted:
                    f.write(job_id + "\n")

        else:
            print("Aucun nouveau job NTLM détecté depuis la dernière exécution.")

    except requests.exceptions.RequestException as e:
        print("Erreur lors de la requête vers hashes.com :", e)

if __name__ == "__main__":
    main()
