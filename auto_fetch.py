import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime, timezone

import config
from startup_summary import fetch_homepage_html, extract_visible_text, generate_startup_paragraph_from_text, extract_structured_data


SHEET_A = "companies_info"
SHEET_B = "employee_history"

credentials = Credentials.from_service_account_info(
    config.google_credentials_json, scopes=config.SCOPES
)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(config.SPREADSHEET_ID).worksheet(SHEET_A)
history_sheet = gc.open_by_key(config.SPREADSHEET_ID).worksheet(SHEET_B)

AUTO_FETCH_FIELDS = ["llm_summary", "employee_count", "total_funding", "capital"]  # when adding new fields, also: 1. update the prompt in extract_structured_data() 2. update the Google Sheets columns 3. update the code below: "write timestamp to column X"


# =====================
# MAIN LOOP
# =====================
def main():
    start_time = time.time()
    rows = sheet.get_all_values()
    headers = rows[0]
    col_idx = {h: i for i, h in enumerate(headers)}
    TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


    # Append timestamp as a new column header
    print(len(history_sheet.row_values(1)))
    history_sheet.update_cell(1, len(history_sheet.row_values(1)) + 1, TIMESTAMP)
    new_col_index = len(history_sheet.row_values(1))

    # Read existing company_id column (column 1)
    history_company_ids = history_sheet.col_values(1)

    company_id_to_row = {
        cid: idx + 1
        for idx, cid in enumerate(history_company_ids)
        if cid != "company_id"
    }


    # assume header row
    for i in range(1, len(rows)):
        urls_cell = rows[i][2]
        summary_cell = rows[i][4]

        # skip if follow_updates = "no"
        if rows[i][3].strip().lower() == "no":
            print("skipped")
            continue

        

        urls = [u.strip() for u in urls_cell.split("\n") if u.strip()]
        if not urls:
            continue

        print(f"Processing row {i+1}...")

        all_text = []
        for url in urls:
            html = fetch_homepage_html(url)
            if not html:
                continue
            text = extract_visible_text(html)
            if text:
                all_text.append(text)

            time.sleep(0.4)  # polite crawling

        if not all_text:
            continue

        combined_text = "\n".join(all_text)

        #print(combined_text)

        #summary = generate_startup_paragraph_from_text(combined_text)
        try:
            data = extract_structured_data(combined_text)
        except Exception as e:
            print("LLM parsing error:", e)
            continue

        # write results back
        updates = []
        for field in AUTO_FETCH_FIELDS:
            if field not in col_idx:
                continue

            value = data.get(field)

            updates.append((i + 1, col_idx[field] + 1, value))

        for row, col, value in updates:
            sheet.update_cell(row, col, "" if value is None else value)

        # write timestamp to column I
        sheet.update_cell(i + 1, 9, TIMESTAMP)

        # write to history sheet
        company_id = rows[i][0]
        company_name = rows[i][1]
        if company_id in company_id_to_row:
            history_row = company_id_to_row[company_id]
        else:
            history_row = len(history_sheet.col_values(1)) + 1
            history_sheet.update_cell(history_row, 1, company_id)
            history_sheet.update_cell(history_row, 2, company_name)
            company_id_to_row[company_id] = history_row
        history_sheet.update_cell(history_row, new_col_index, data.get("employee_count"))

        time.sleep(2)  # LLM rate safety

    elapsed_time = time.time() - start_time
    print(f"Done. Total running time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")


if __name__ == "__main__":
    main()


# update_cell is 1-based indexing