import requests
BASE_URL = "https://historical.api.jobtechdev.se/search"

def fetch_ads(limit: int = 10):
    params = {
        "limit": limit,
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return payload["hits"]