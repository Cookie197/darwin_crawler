## environment

* Google cloud project
* Enable Google Sheets API
    * APIs & Services → Library
    * Enable Google Sheets API
    * IAM & Admin → Service Accounts
    * Create Service Account
    * Create JSON key → download it
* Create Google sheets manually, share it with the Service Account (edit access)

* **Currently, the project is using my personal google cloud account and Gemini API. For migration, create a new google cloud project and do the above operations. Update the ``GOOGLE_CREDENTIALS_JSON`` tab in github secrets. Same for Gemini API and google sheet ID.**

## config.py
Contains shared (environment) variables. UPD: also loads secret variables from ``.env`` by using ``load_dotenv()`` and ``os.environ.get()``.

Call ``import config``. Then the variables can be used by calling ``config.[VARIABLE]``.


## testcrawl.py (not in use)
Fetches rows from https://startup-db.com/companies and turns them into csv or uploads to google sheets (imports from ``upload_to_google_sheets.py``).
Then, follow the link company_url (ex. https://startup-db.com/companies/0QVwG3zU48mJ6Eye) to get homapage_url (ex. https://tohakusha.com/), and generate a summary using ``startup_summary.py``. Appends it to the sheets as a separate column.

* needs enterprise account to have full access

## startup_summary.py

> requests, beautifulsoup, playwright, gemini API

Given homepage url, it fetches homepage html (static or dynamic) -> extracts text -> creates summary of startup using **Gemini-3-flash**

* Gemini API free tier only offers 20 requests per day.

``llm_summary(homepage_url)``: given url, returns summary 

``generate_startup_paragraph(homepage_html)``: given html, returns summary

``generate_startup_paragraph_from_text(text)``: given text (or combined text from multiple sites), returns summary

``extract_structured_data(text)``: given text (or combined text from multiple sites), return **structured json** that contatins multiple fields (llm_summary, employee_count, total_funding, etc.) with *one* LLM query. Remember to modify the prompt in the function.



## upload_to_google_sheets.py

> SPREADSHEET_ID, SHEET_NAME, json file

``upload_to_google_sheets(rows)``: write the rows to the particular sheet, *rows* is a list of parsed dicts each containing the data of a startup

## auto_fetch.py  (current main function is here)

> gspread, google.oauth2

uses functions from ``startup_summary.py``

1. Connects to Google Sheets via service account credentials
2. Reads all company rows from the "companies_info" sheet
3. For each company with follow_updates = "yes":
    - Fetches HTML from all provided URLs
    - Extracts visible text content
    - Sends combined text to LLM for structured data extraction
    - Updates main sheet with: llm_summary, employee_count, total_funding
    - Appends employee count to the "employee_history" sheet with current timestamp

## google looker studio

create a new sheet ``employee_history_t`` and enter the formula ``=TRANSPOSE(employee_history!A:ZZZ)`` in cell A1. Now ``employee_history_t`` will automatically mirror ``employee_history`` in transposed form and stay up to date as the source sheet changes.

In google looker studio, create a **time series chart** (not a line chart). Set the x-axis to "date" and specify the data type as "date hour minute". For the y-axes, choose the IDs of the companies you want to track. In the "style" tab, turn on "show points" for each line, and choose "linear interpolation" for the "missing data" option to ensure continuous lines.

Whenever a new company is added to ``employee_history``, it is required to click the "refresh data" button and manually drag the new company ID to the y-axis tab.

## .env

saves secrets locally. Should not be commited to github.

```
GEMINI_API_KEY
GEMINI_MODEL
SPREADSHEET_ID
GOOGLE_CREDENTIALS_JSON
```

The above will also be set in github repo secrets, with the same names.

## cron (if you want local run)

``0 15 * * * /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 /Users/easonchiou/STUFF/code/__darwin/auto_fetch.py 2>/Users/easonchiou/STUFF/code/__darwin/log.txt``

## github actions

Push project to github. Also add ``.gitignore``. Secrets should not appear in commited files, they should be manually added to repo->settings->secrets.

```
One-time setup:
ssh-keygen -t ed25519 -C "your@email.com"

Add the public key (~/.ssh/id_ed25519.pub) to:

GitHub → Settings → SSH keys

Then switch your repo remote:

git remote set-url origin git@github.com:yourname/your-repo.git
git push
```

Add file ``.github/workflows/crawler.yml`` to setup github actions.
