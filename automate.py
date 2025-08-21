
import json
import time
import requests
from lxml import html
import re
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# Load variables from .env into os.environ
load_dotenv()
# === CONFIG ===
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"
TABLE_XPATH = "//*[@id='mw-content-text']/div[1]/table[4]"
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(),f"{os.environ.get('GOOGLE-SHEET-JSON')}")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ.get("SPREADSHEET-ID")
RANGE = "Sheet1!A:D"
VALUE_INPUT_OPTION = "RAW"
INSERT_OPTION = "INSERT_ROWS"

# Setup Google Sheets API client
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)

def append_to_sheets(values, max_retries=3):
    body = {"majorDimension": "ROWS", "values": values}
    attempt = 0
    while attempt < max_retries:
        try:
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE,
                valueInputOption=VALUE_INPUT_OPTION,
                insertDataOption=INSERT_OPTION,
                body=body
            ).execute()
            return result

        except HttpError as e:
            status = e.resp.status
            try:
                error_content = json.loads(e.content.decode("utf-8"))
                error_message = error_content.get("error", {}).get("message", "")
                error_reason = (
                    error_content.get("error", {})
                    .get("errors", [{}])[0]
                    .get("reason", "")
                )
            except Exception:
                error_message = str(e)
                error_reason = ""

            print(f"[Error {status}] {error_message} (reason: {error_reason})")

            if status in (401, 403, 404):
                # Unrecoverable errors
                print("Stopping due to unrecoverable error.")
                return None

            elif status in (429, 500, 503):
                # Retry with exponential backoff
                retry_after = int(e.resp.get("Retry-After", "5"))
                wait_time = retry_after * (2 ** attempt)
                print(f"{status} → waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                attempt += 1
                continue

            else:
                print(f"Unrecoverable error {status}. Full response: {e.content}")
                return None

    print("Max retries reached, giving up.")
    return None


# === STEP 1 & 2: Load page and extract table via XPath ===
resp = requests.get(WIKI_URL)
if resp.status_code != 200 or "<body" not in resp.text:
    raise RuntimeError("Failed to load Wikipedia page")
tree = html.fromstring(resp.content)
table = tree.xpath(TABLE_XPATH)
if not table:
    raise RuntimeError("Could not find the finals table with provided XPath")
table = table[0]

# === STEP 3: Loop through the first 10 rows ===
rows = table.xpath("./tbody/tr[position() >= 2 and position() <= 11]")

def normalize_year(text):
    try:
        year = int(re.search(r"\d{4}", text).group())
        return year if 1900 <= year <= 2080 else text.strip()
    except Exception:
        return text.strip()

def normalize_text(cell):
    text = "".join(cell.xpath(".//text()")).strip()
    return " ".join(text.split())

# Extract and append each row individually (or batch for efficiency)
batch_values = []
for row in rows:
    cells = row.xpath("./td|./th")
    if len(cells) < 4:
        continue
    year_raw = normalize_text(cells[0])
    year = normalize_year(year_raw)
    winner = normalize_text(cells[1])
    score = normalize_text(cells[2])
    runners_up = normalize_text(cells[3])

    print(f"Collected: {year}, {winner}, {score}, {runners_up}")
    batch_values.append([year, winner, score, runners_up])

# === Append all at once ===
if batch_values:
    print("Appending all rows in one batch...")
    result = append_to_sheets(batch_values)
    if result:
        print("Successfully appended batch to Google Sheets.")
