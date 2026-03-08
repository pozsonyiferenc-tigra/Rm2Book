import time
import requests


class RedmineClient:
    """Redmine REST API kliens automatikus paginálással és retry logikával."""

    def __init__(self, base_url, api_key, max_retries=3):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        })

    def get(self, endpoint, params=None):
        """Egyetlen GET kérés retry logikával."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                print(f"  [!] Hiba ({e}), újrapróbálás {wait}s múlva...")
                time.sleep(wait)

    def get_all(self, endpoint, resource_key, params=None, on_progress=None):
        """Paginált GET: az összes rekord lekérése.

        Args:
            endpoint: API végpont
            resource_key: A JSON válasz kulcsa (pl. "issues", "news")
            params: Extra query paraméterek
            on_progress: Callback(fetched_count, total_count)

        Returns:
            Az összes rekord listája.
        """
        all_items = []
        offset = 0
        limit = 100
        total = None

        while True:
            p = {"offset": offset, "limit": limit}
            if params:
                p.update(params)
            data = self.get(endpoint, params=p)
            if data is None:
                break

            items = data.get(resource_key, [])
            total = data.get("total_count", len(items))
            all_items.extend(items)

            if on_progress:
                on_progress(len(all_items), total)

            if len(all_items) >= total:
                break
            offset += limit

        return all_items
