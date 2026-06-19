"""
Google Sheets I/O via service account. Reads 'Pending' rows, writes live URL + 'Done'.

Sheet columns (row 1 = headers):
  A ClientName  B Industry  C Location  D Services  E Colors  F Phone
  G Email  H Images(URL)  I Audience  J Requirements  K DesignStyle
  L Status (Pending/Done/Error)  M LiveURL  N DoneAt (date, used for daily cap)

Setup: create a Google Cloud service account, download JSON key -> .gcp_sa.json here,
enable Google Sheets API, and SHARE the sheet with the service-account email (Editor).
Set SHEET_ID in .env.
"""
import os, datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

HERE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SA_FILE = os.path.join(HERE, ".gcp_sa.json")
TAB = os.environ.get("SHEET_TAB", "Sheet1")
RANGE = f"{TAB}!A2:N"   # data rows (skip header)

STATUS_COL = "L"
URL_COL = "M"
DONE_COL = "N"
FIELDS = ["name", "industry", "location", "services", "colors", "phone",
          "email", "images", "audience", "requirements", "design_style",
          "status", "url", "done_at"]


def _svc():
    creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets()


def read_pending(sheet_id):
    """Return list of dicts for rows whose Status is blank or 'Pending'. Includes 'row' (sheet row number)."""
    svc = _svc()
    vals = svc.values().get(spreadsheetId=sheet_id, range=RANGE).execute().get("values", [])
    out = []
    for i, row in enumerate(vals):
        row = row + [""] * (len(FIELDS) - len(row))
        rec = dict(zip(FIELDS, row))
        rec["row"] = i + 2  # +2: header is row 1, data starts row 2
        status = (rec.get("status") or "").strip().lower()
        if status in ("", "pending"):
            if (rec.get("name") or "").strip():   # skip empty rows
                out.append(rec)
    return out


def mark(sheet_id, row, status, url=None, done_at=None):
    svc = _svc()
    data = [{"range": f"{TAB}!{STATUS_COL}{row}", "values": [[status]]}]
    if url is not None:
        data.append({"range": f"{TAB}!{URL_COL}{row}", "values": [[url]]})
    if done_at is not None:
        data.append({"range": f"{TAB}!{DONE_COL}{row}", "values": [[done_at]]})
    svc.values().batchUpdate(spreadsheetId=sheet_id,
                             body={"valueInputOption": "RAW", "data": data}).execute()


def done_today_count(sheet_id):
    """Count rows whose DoneAt (col N) is today's date — the daily-cap ledger (survives ephemeral runners)."""
    today = datetime.date.today().isoformat()
    svc = _svc()
    vals = svc.values().get(spreadsheetId=sheet_id,
                            range=f"{TAB}!{DONE_COL}2:{DONE_COL}").execute().get("values", [])
    return sum(1 for r in vals if r and str(r[0]).startswith(today))


if __name__ == "__main__":
    import sys
    sid = os.environ.get("SHEET_ID") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not sid:
        raise SystemExit("usage: SHEET_ID=... python sheets_client.py")
    rows = read_pending(sid)
    print(f"{len(rows)} pending rows:")
    for r in rows:
        print(f"  row {r['row']}: {r['name']} / {r['industry']} / {r['location']}")
