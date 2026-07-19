"""
Microsoft tool — read-only access to Outlook mail, Calendar, and OneDrive
via Microsoft Graph API.

Setup:
1. Go to https://portal.azure.com -> Azure Active Directory -> App registrations -> New registration
   - Name: Companion (or anything)
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: leave blank (we use device code flow, no redirect needed)
2. After creating, copy the "Application (client) ID"
3. Put it in core/.env as MS_CLIENT_ID=...
4. No client secret needed — device code flow is designed for apps like this one.

First run will print a URL + code — open the URL, enter the code, sign in.
After that, a local token cache file lets you skip re-login until the token expires.
"""

import msal
from pathlib import Path
from config import MS_CLIENT_ID, MS_TENANT_ID

AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"

# Read-only scopes only, matching the "read-only" access level chosen for Avcore.
SCOPES = ["Mail.Read", "Calendars.Read", "Files.Read"]

TOKEN_CACHE_PATH = Path(__file__).parent / "ms_token_cache.bin"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())
    return cache


def _save_cache(cache: msal.SerializableTokenCache):
    if cache.has_state_changed:
        TOKEN_CACHE_PATH.write_text(cache.serialize())


def _get_token() -> str | None:
    if not MS_CLIENT_ID:
        return None

    cache = _load_cache()
    app = msal.PublicClientApplication(MS_CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            return None
        print(flow["message"])  # e.g. "Go to https://microsoft.com/devicelogin and enter code ABC123"
        result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache)
    return result.get("access_token") if result else None


def _graph_get(path: str, params: dict | None = None) -> dict:
    import requests
    token = _get_token()
    if not token:
        return {"error": "Not authenticated. Set MS_CLIENT_ID in core/.env and run again to log in."}

    res = requests.get(
        f"{GRAPH_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=15,
    )
    if res.status_code != 200:
        return {"error": f"Graph API error {res.status_code}: {res.text}"}
    return res.json()


def get_recent_emails(limit: int = 5) -> list[dict]:
    data = _graph_get("/me/messages", params={"$top": limit, "$select": "subject,from,receivedDateTime,bodyPreview"})
    if "error" in data:
        return [data]
    return [
        {
            "subject": m.get("subject"),
            "from": m.get("from", {}).get("emailAddress", {}).get("address"),
            "received": m.get("receivedDateTime"),
            "preview": m.get("bodyPreview"),
        }
        for m in data.get("value", [])
    ]


def get_upcoming_events(limit: int = 5) -> list[dict]:
    data = _graph_get("/me/events", params={"$top": limit, "$select": "subject,start,end,location"})
    if "error" in data:
        return [data]
    return [
        {
            "subject": e.get("subject"),
            "start": e.get("start", {}).get("dateTime"),
            "end": e.get("end", {}).get("dateTime"),
            "location": e.get("location", {}).get("displayName"),
        }
        for e in data.get("value", [])
    ]


# Quick manual test: `python core/tools/microsoft.py`
if __name__ == "__main__":
    print("Recent emails:")
    for e in get_recent_emails():
        print(e)
    print("\nUpcoming events:")
    for e in get_upcoming_events():
        print(e)