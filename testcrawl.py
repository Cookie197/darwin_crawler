'''
会社概要
https://wevnal.io/about#company
https://basicinc.jp/company
https://sotas.co.jp/corporate/info/
https://www.lion.co.jp/ja/company/about/
https://onecapital.jp/company-info
https://www.on-grit.com/company-guide/
https://www.omcon.co.jp/company/access/
'''

import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


from upload_to_google_sheets import upload_to_google_sheets
from startup_summary import llm_summary
import config



BASE_URL = "https://startup-db.com/companies"
OUTPUT_FILE = "startups.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://startup-db.com/",
}
session = requests.Session()
session.headers.update(HEADERS)



def extract_homepage_url(html):
    soup = BeautifulSoup(html, "html.parser")

    for dt in soup.select("dt"):
        if dt.get_text(strip=True) == "HP":
            dd = dt.find_next_sibling("dd")
            if not dd:
                return None

            link = dd.find("a", href=True)
            return link["href"] if link else None
    return None


def fetch_page_html(url):
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text



# get homepage (ex. https://tohakusha.com/) from company url (ex. https://startup-db.com/companies/0QVwG3zU48mJ6Eye)
def get_homepage_from_company_url(company_url):
    try:
        html = fetch_page_html(company_url)
        return extract_homepage_url(html)
    except requests.HTTPError as e:
        print(f"Failed to fetch detail page: {company_url} ({e})")
        return None



def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

def parse_startup_row(tr):
    def text_or_none(selector):
        el = tr.select_one(selector)
        return el.get_text(strip=True) if el else None

    def texts(selector):
        return [e.get_text(strip=True) for e in tr.select(selector)]

    data = {}

    # Company name
    data["company_name"] = text_or_none("span[class*='CompanyNameCell_companyName']")

    # Company logo
    #logo = tr.select_one("img[class*='CompanyNameCell_companyLogo']")
    #data["logo_url"] = logo["src"] if logo else None

    # Company detail page URL
    link = tr.select_one("a[href^='/companies/']")
    data["company_url"] = urljoin(BASE_URL, link["href"]) if link else None

    # Funding stage
    data["funding_stage"] = text_or_none("span[class*='SeriesCell']")

    # Capital type
    data["capital_type"] = text_or_none("span[class*='CapitalTypeCell']")

    # Listing status
    data["listing_status"] = text_or_none("span[class*='ListingTypeCell']")

    # Description
    data["description"] = text_or_none("span[class*='DescriptionCell']")

    # Established date
    data["established_date"] = text_or_none("span[class*='EstablishedDateCell']")

    # Employee count
    data["employee_count"] = text_or_none("span[class*='EmployeeNumberCell']")

    # Market cap
    data["market_cap"] = text_or_none("span[class*='MarketCapCell']")

    # Total funding
    data["total_funding"] = text_or_none("span[class*='TotalFundingAmountCell']")

    # Last funded date
    data["last_funded_date"] = text_or_none("span[class*='LastFundedDateCell']")

    # Prefecture
    data["prefecture"] = text_or_none("span[class*='PrefectureCell']")

    # Tags
    data["tags"] = texts("button[class*='TagItems_tagLink']")

    # Number of patents
    data["patent_count"] = text_or_none("div[class*='NumberOfPatentCell']")

    # Created / updated dates
    data["created_date"] = text_or_none("span[class*='CreatedDateCell']")
    data["updated_date"] = text_or_none("span[class*='UpdatedDateCell']")

    data["homepage_url"] = get_homepage_from_company_url(data["company_url"])
    if not data["homepage_url"]:
        data["llm_summary"] = None
    else:
        data["llm_summary"] = llm_summary(data["homepage_url"])

    return data


def crawl_list_page(url):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    #resp = requests.get(url, timeout=15)
    #resp.raise_for_status()

    #soup = BeautifulSoup(resp.text, "html.parser")

    startups = []
    for tr in soup.select("tr"):
        if len(startups) >= 4:
            break
        if tr.select_one("span[class*='CompanyNameCell_companyName']"):
            startups.append(parse_startup_row(tr))

    return startups

def write_csv(rows, filename=OUTPUT_FILE):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=config.CSV_FIELDS)
        writer.writeheader()

        for row in rows:
            clean_row = row.copy()

            # join tags list into string
            if isinstance(clean_row.get("tags"), list):
                clean_row["tags"] = "|".join(clean_row["tags"])

            writer.writerow(clean_row)

if __name__ == "__main__":
    url = "https://startup-db.com/companies" 
    results = crawl_list_page(url)

    #for r in results:
     #   print(r)
    #write_csv(results)
    upload_to_google_sheets(results)

