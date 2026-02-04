import gspread
from google.oauth2.service_account import Credentials

import config as CONFIG

#SPREADSHEET_ID = "1S_Fd8p_irAsaW7H6UYkP-bAjoudbP9x95gdprUP7OtI"
SHEET_NAME = "darwin_test"

'''SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]'''



def upload_to_google_sheets(rows):
    creds = Credentials.from_service_account_info(
        CONFIG.google_credentials_json, scopes=CONFIG.SCOPES
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(CONFIG.SPREADSHEET_ID)

    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
        sheet.clear()
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(
            title=SHEET_NAME,
            rows=1000,
            cols=len(CONFIG.CSV_FIELDS),
        )

    values = [CONFIG.CSV_FIELDS]

    for row in rows:
        record = []
        for field in CONFIG.CSV_FIELDS:
            value = row.get(field)

            if isinstance(value, list):
                value = "|".join(value)

            record.append(value)

        values.append(record)

    sheet.update(values, value_input_option="RAW")


# Example:
# startups = crawl_list_page(url)
# upload_to_google_sheets(startups)
