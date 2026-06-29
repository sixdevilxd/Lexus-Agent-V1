"""Klien GitHub lengkap menggunakan requests (Termux-friendly, tanpa SDK berat).
Semua fungsi memakai access_token milik pengguna yang sedang login."""
import requests
import base64

API = "https://api.github.com"


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ---------------- BACA ----------------
def list_repos(token, max_results=30):
    """Daftar repositori milik pengguna (terbaru diupdate lebih dulu)."""
    url = f"{API}/user/repos"
    params = {"per_page": max_results, "sort": "updated", "affiliation": "owner"}
    r = requests.get(url, headers=_headers(token), params=params, timeout=30)
    if r.status_code != 200:
        return {"status": "error", "message": r.text}
    repos = [{
        "name": x["name"],
        "full_name": x["full_name"],
        "private": x["private"],
        "description": x.get("description"),
        "url": x["html_url"],
        "default_branch": x.get("default_branch", "main"),
    } for x in r.json()]
    return {"status": "success", "count": len(repos), "repos": repos}


def read_file(token, repo_owner, repo_name, file_path, branch="main"):
    """Baca isi satu file teks."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    r = requests.get(url, headers=_headers(token), params={"ref": branch}, timeout=30)
    if r.status_code == 200:
        data = r.json()
        enc = data.get("content", "").replace("\n", "").replace("\r", "")
        decoded = base64.b64decode(enc).decode("utf-8", errors="ignore")
        return {"status": "success", "content": decoded, "sha": data.get("sha")}
    if r.status_code == 404:
        return {"status": "error", "message": "File tidak ditemukan (404)."}
    return {"status": "error", "message": r.text}


def list_directory(token, repo_owner, repo_name, dir_path="", branch="main"):
    """Daftar isi sebuah folder/direktori di repositori."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/contents/{dir_path}"
    r = requests.get(url, headers=_headers(token), params={"ref": branch}, timeout=30)
    if r.status_code != 200:
        return {"status": "error", "message": r.text}
    data = r.json()
    if not isinstance(data, list):
        return {"status": "error", "message": "Path ini adalah file, bukan folder."}
    items = [{"name": x["name"], "type": x["type"], "path": x["path"]} for x in data]
    return {"status": "success", "count": len(items), "items": items}


def list_issues(token, repo_owner, repo_name, state="open", max_results=20):
    """Daftar issue di repositori."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/issues"
    params = {"state": state, "per_page": max_results}
    r = requests.get(url, headers=_headers(token), params=params, timeout=30)
    if r.status_code != 200:
        return {"status": "error", "message": r.text}
    issues = [{
        "number": x["number"], "title": x["title"], "state": x["state"],
        "url": x["html_url"], "is_pull_request": "pull_request" in x,
    } for x in r.json()]
    return {"status": "success", "count": len(issues), "issues": issues}


# ---------------- TULIS ----------------
def commit_and_push_file(token, repo_owner, repo_name, file_path, file_content, commit_message, branch="main"):
    """Buat / update file dalam satu commit."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    sha = None
    r_get = requests.get(url, headers=_headers(token), params={"ref": branch}, timeout=30)
    if r_get.status_code == 200:
        sha = r_get.json().get("sha")
    encoded = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
    payload = {"message": commit_message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code in (200, 201):
        return {"status": "success", "message": f"Berhasil push ke {file_path}!",
                "url": r.json()["content"]["html_url"]}
    return {"status": "error", "message": r.text}


def delete_file(token, repo_owner, repo_name, file_path, commit_message, branch="main"):
    """Hapus sebuah file (butuh SHA terbaru)."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    r_get = requests.get(url, headers=_headers(token), params={"ref": branch}, timeout=30)
    if r_get.status_code != 200:
        return {"status": "error", "message": "File tidak ditemukan untuk dihapus."}
    sha = r_get.json().get("sha")
    payload = {"message": commit_message, "sha": sha, "branch": branch}
    r = requests.delete(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 200:
        return {"status": "success", "message": f"File {file_path} berhasil dihapus."}
    return {"status": "error", "message": r.text}


def create_repo(token, name, private=True, description=""):
    """Buat repositori baru milik pengguna."""
    url = f"{API}/user/repos"
    payload = {"name": name, "private": private, "description": description, "auto_init": True}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 201:
        d = r.json()
        return {"status": "success", "message": f"Repo {name} dibuat!", "url": d["html_url"]}
    return {"status": "error", "message": r.text}


def create_branch(token, repo_owner, repo_name, new_branch, from_branch="main"):
    """Buat branch baru dari branch sumber."""
    ref_url = f"{API}/repos/{repo_owner}/{repo_name}/git/ref/heads/{from_branch}"
    r_ref = requests.get(ref_url, headers=_headers(token), timeout=30)
    if r_ref.status_code != 200:
        return {"status": "error", "message": f"Branch sumber '{from_branch}' tidak ditemukan."}
    sha = r_ref.json()["object"]["sha"]
    url = f"{API}/repos/{repo_owner}/{repo_name}/git/refs"
    payload = {"ref": f"refs/heads/{new_branch}", "sha": sha}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 201:
        return {"status": "success", "message": f"Branch '{new_branch}' dibuat dari '{from_branch}'."}
    return {"status": "error", "message": r.text}


def create_pull_request(token, repo_owner, repo_name, title, head, base="main", body=""):
    """Buat Pull Request dari branch `head` ke `base`."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/pulls"
    payload = {"title": title, "head": head, "base": base, "body": body}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 201:
        d = r.json()
        return {"status": "success", "message": f"PR #{d['number']} dibuat!", "url": d["html_url"]}
    return {"status": "error", "message": r.text}


def create_issue(token, repo_owner, repo_name, title, body=""):
    """Buat issue baru."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/issues"
    payload = {"title": title, "body": body}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 201:
        d = r.json()
        return {"status": "success", "message": f"Issue #{d['number']} dibuat!", "url": d["html_url"]}
    return {"status": "error", "message": r.text}


def comment_issue(token, repo_owner, repo_name, issue_number, body):
    """Balas / komentari sebuah issue atau PR."""
    url = f"{API}/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
    payload = {"body": body}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code == 201:
        return {"status": "success", "message": f"Komentar ditambahkan ke #{issue_number}.",
                "url": r.json()["html_url"]}
    return {"status": "error", "message": r.text}
