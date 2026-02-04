import re
import requests
import json
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

import config

#HOMEPAGE_URL = 'https://www.on-grit.com/'
#HOMEPAGE_URL = 'https://www.supwat.com/'
HOMEPAGE_URL = 'https://tohakusha.com/'

# Setup Gemini API
client = genai.Client(api_key=config.gemini_api_key)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

def fetch_homepage_html_static(url: str, timeout=15) -> str:
    """
    Fetch homepage HTML with headers that work for most Japanese startup sites.
    """
    
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text

def fetch_homepage_html_dynamic(url: str, timeout=15000) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
        )

        page.goto(url, timeout=timeout, wait_until="domcontentloaded") # network_idle -> domcontentloaded
        html = page.content()
        browser.close()

    return html

def fetch_homepage_html(url):
    try:
        html = fetch_homepage_html_static(url)
        if len(extract_visible_text(html)) > 1000:
            return html
    except Exception:
        pass

    return fetch_homepage_html_dynamic(url)


def extract_visible_text(html: str, max_chars=6000) -> str:
    """
    Strip scripts/styles and return main visible text.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n+", "\n", text)
    text = text.strip()

    return text[:max_chars]

def generate_startup_paragraph(homepage_html: str) -> str:
    homepage_text = extract_visible_text(homepage_html)
    with open("homepage_text.txt", 'w') as f:
        f.write(homepage_text)

    system_prompt = """
    You are a venture analyst specializing in Japanese startups.
    You infer business models even when information is vague or marketing-heavy.
    Be concrete and avoid buzzwords.
    """

    user_prompt = f"""
    Below is the text content from a Japanese startup's homepage.

    Analyze it and write ONE concise paragraph (3 to 5 English sentences) that answers:

    1. What the company does (product/service)
    2. Why it matters (specific problem solved and real wedge or value)
    3. Who pays (customer, and buyer if enterprise)

    Rules:
    - If the text provides little to no information, raise an error instead of writing a paragraph.
    - Infer missing details if necessary, but stay realistic
    - Prefer specific customers over generic terms
    - Do NOT quote the homepage
    - Do NOT use bullet points

    Homepage text:
    \"\"\"
    {homepage_text}
    \"\"\"
    """


    # Generate content
    response = client.models.generate_content(
        model=config.gemini_model,
        config=types.GenerateContentConfig(system_instruction = system_prompt),
        contents=user_prompt,
    )

    return response.text.strip()

def generate_startup_paragraph_from_text(homepage_text: str) -> str:
    homepage_html = f"<html><body><pre>{homepage_text}</pre></body></html>"
    return generate_startup_paragraph(homepage_html)


def extract_structured_data(combined_text):
    prompt = f"""
You are extracting structured company data.

ONLY use the information explicitly stated in the text.
If a value cannot be found, return null for that field.
Do NOT guess.

Return STRICT JSON with the following schema:

{{
  "llm_summary": string | null,
  "employee_count": string | null,
  "total_funding": string | null,
  "capital": string | null,
}}

For the employee_count, strongly prefer exact numbers (e.g., "42") over ranges (e.g., "~50").

For total_funding and capital, return the amount (a number) in Japanese yen (e.g., "500,000,000").

For the llm_summary, you are a venture analyst specializing in Japanese startups. You infer business models even when information is vague or marketing-heavy.
Be concrete and avoid buzzwords. Analyze the text and write ONE concise paragraph (3 to 5 English sentences) that answers:

1. What the company does (product/service)
2. Why it matters (specific problem solved and real wedge or value)
3. Who pays (customer, and buyer if enterprise)

Rules:
- If the text provides little to no information, return null instead of writing a paragraph.
- Infer missing details if necessary, but stay realistic
- Prefer specific customers over generic terms
- Do NOT quote the homepage
- Do NOT use bullet points

TEXT:
{combined_text}
"""

    # Generate content
    response = client.models.generate_content(
        model=config.gemini_model,
        contents=prompt,
    )

    content = response.text.strip()[8:-4]  # remove ```json and ```
    print(content)
    
    return json.loads(content)


'''
# Example usage
if __name__ == "__main__":
    # Ensure homepage.html exists in your directory
    try:
        with open('homepage.html', "r", encoding="utf-8") as f:
            html = f.read()

        paragraph = generate_startup_paragraph(html)
        print(paragraph)
    except FileNotFoundError:
        print("Please ensure 'homepage.html' is in the same directory.")
'''

def llm_summary(homepage_url):
    html = fetch_homepage_html(homepage_url)
    paragraph = generate_startup_paragraph(html)
    return paragraph

if __name__ == "__main__":
    html = fetch_homepage_html(HOMEPAGE_URL)
    paragraph = generate_startup_paragraph(html)

    print(paragraph)

