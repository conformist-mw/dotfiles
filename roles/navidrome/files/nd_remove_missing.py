import httpx
import os


USERNAME = os.getenv("ND_USERNAME")
PASSWORD = os.getenv("ND_PASSWORD")
BASE_URL = os.getenv("ND_BASE_URL")
login_url = f"{BASE_URL}/auth/login"
missing_url = f"{BASE_URL}/api/missing"


def login():
    with httpx.Client() as client:
        response = client.post(
            login_url,
            json={"username": USERNAME, "password": PASSWORD},
        )
        response.raise_for_status()
        token = response.json()["token"]
        with open("token.txt", "w") as file:
            file.write(token)
        return token


def load_token():
    try:
        with open("token.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return None


def fetch_missing(token):
    with httpx.Client() as client:
        response = client.get(
            missing_url,
            headers={"X-ND-Authorization": f"Bearer {token}"},
            params={"_start": 0, "_end": 50},
        )
        response.raise_for_status()
        return response.json()


def delete_missing(token, ids):
    query_params = "&".join([f"id={id}" for id in ids])
    with httpx.Client() as client:
        response = client.delete(
            f"{missing_url}?{query_params}",
            headers={"X-ND-Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    token = load_token()
    try:
        response = fetch_missing(token)
    except httpx.HTTPError as e:
        token = login()

    attempt = 2
    while attempt > 0:
        try:
            response = fetch_missing(token)
            if len(response) == 0:
                break
            ids = [item["id"] for item in response]
            response = delete_missing(token, ids)
        except Exception:
            attempt -= 1
