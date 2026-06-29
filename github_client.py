import requests
import base64

def read_file(token, repo_owner, repo_name, file_path, branch="main"):
    """
    Membaca isi file dari repositori GitHub menggunakan token pengguna.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers, params={"ref": branch})
    if response.status_code == 200:
        data = response.json()
        encoded_content = data.get("content", "")
        # Remove any newlines and decode
        encoded_content = encoded_content.replace("\n", "").replace("\r", "")
        decoded_content = base64.b64decode(encoded_content).decode("utf-8", errors="ignore")
        return {
            "status": "success",
            "content": decoded_content,
            "sha": data.get("sha"),
            "size": data.get("size")
        }
    elif response.status_code == 404:
        return {"status": "error", "message": "File tidak ditemukan (404)."}
    else:
        return {"status": "error", "message": f"Gagal membaca file: {response.text}"}


def commit_and_push_file(token, repo_owner, repo_name, file_path, file_content, commit_message, branch="main"):
    """
    Membuat commit baru / memperbarui file di repositori GitHub menggunakan token pengguna.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Ambil SHA file jika file sudah ada (dibutuhkan oleh GitHub untuk update)
    sha = None
    r_get = requests.get(url, headers=headers, params={"ref": branch})
    if r_get.status_code == 200:
        sha = r_get.json().get("sha")

    # Encode isi file ke base64
    encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

    # Push commit
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    r_put = requests.put(url, headers=headers, json=payload)
    if r_put.status_code in [200, 201]:
        return {
            "status": "success",
            "message": f"Berhasil push ke {file_path}!",
            "url": r_put.json()["content"]["html_url"]
        }
    else:
        return {"status": "error", "message": f"Gagal push file: {r_put.text}"}
