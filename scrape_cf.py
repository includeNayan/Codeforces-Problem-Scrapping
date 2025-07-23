# cf_scraper.py
import re
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Setup Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=options)

# Helper to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Helper to clean text
def clean_text(tag):
    return tag.get_text(" ", strip=True) if tag else ""

def get_text_lines(tag):
    return tag.get_text("\n", strip=True) if tag else ""

# Fetch editorial content via requests
def fetch_editorial_content(url):
    try:
        headers = {"User-Agent": options.arguments[-1]}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        art = soup.select_one(".ttypography")
        return art.get_text("\n", strip=True) if art else None
    except Exception:
        return None

try:
    url = "https://codeforces.com/contest/2107/problem/F2 "
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "problem-statement"))
    )

    # Extract identifiers
    m = re.search(r'/contest/(\d+)/problem/([A-Z])', url) or \
        re.search(r'/problemset/problem/(\d+)/([A-Z])', url)
    contest_id = m.group(1) if m else "unknown"
    problem_index = m.group(2) if m else "X"

    # Extract title
    title = driver.find_element(By.CLASS_NAME, "title").text.strip()

    # Structured parse
    html = driver.find_element(By.CLASS_NAME, "problem-statement").get_attribute("innerHTML")
    soup = BeautifulSoup(html, "html.parser")

    description   = clean_text(soup.select_one(".header + div"))
    input_sec     = clean_text(soup.select_one(".input-specification"))
    output_sec    = clean_text(soup.select_one(".output-specification"))
    example       = get_text_lines(soup.select_one(".sample-tests"))
    note          = clean_text(soup.select_one(".note"))

    # Tags
    tags = [t.text.strip() for t in driver.find_elements(By.CSS_SELECTOR, ".roundbox .tag-box")]

    # Editorial link
    try:
        tutorial_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Tutorial").get_attribute("href")
    except:
        tutorial_link = None

    # Fetch editorial via requests
    editorial_content = fetch_editorial_content(tutorial_link) if tutorial_link else None

    # Build JSON
    problem_data = {
        "contest_id": contest_id,
        "problem_index": problem_index,
        "title": title,
        "description": description,
        "input": input_sec,
        "output": output_sec,
        "example": example,
        "note": note,
        "tags": tags,
        "editorial_content": editorial_content
    }

    filename = f"{sanitize_filename(title)}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(problem_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Problem saved to {filename}")

except Exception as e:
    print("❌ Error extracting content:", e)

finally:
    driver.quit()
