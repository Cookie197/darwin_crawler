import os
from dotenv import load_dotenv
import json

load_dotenv()  # reads .env if it exists

def get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value



CSV_FIELDS = [
    "company_name",
    "company_url",
    "homepage_url",
    "funding_stage",
    "capital_type",
    "listing_status",
    "description",
    "llm_summary",
    "established_date",
    "employee_count",
    "market_cap",
    "total_funding",
    "last_funded_date",
    "prefecture",
    "tags",
    "patent_count",
    "created_date",
    "updated_date",
    #"logo_url",
]

gemini_api_key = get_env("GEMINI_API_KEY")
#gemini_model = 'gemini-3-flash-preview'
gemini_model = get_env("GEMINI_MODEL")


SPREADSHEET_ID = get_env("SPREADSHEET_ID")
#SHEET_NAME = "darwin_test"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


google_credentials_json = json.loads(get_env("GOOGLE_CREDENTIALS_JSON"))