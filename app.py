import random
import json
import os
from curl_cffi import requests as cffi_requests # For scraping (bypassing blocks)
import requests # For sending data to Make (standard requests is fine here)
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Browse page showing upcoming training courses
BASE_URL = "https://www.salto-youth.net"
BROWSE_URL = "https://www.salto-youth.net/tools/european-training-calendar/browse/"

def get_random_course():
    print("🚀 Starting Scraper...")
    
    # 1. Setup Session (Mimic Chrome to avoid blocking)
    session = cffi_requests.Session(impersonate="chrome")

    try:
        # 2. Get the list of courses
        print(f"🔍 Fetching course list from: {BROWSE_URL}")
        response = session.get(BROWSE_URL, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        # 3. Find all course links
        # SALTO course links usually contain "/training/" in the href
        all_links = soup.find_all("a", href=True)
        course_links = [
            link['href'] for link in all_links 
            if "/tools/european-training-calendar/training/" in link['href'] 
            and "apply" not in link['href'] # Avoid 'apply now' buttons if they exist separately
            and ".html" not in link['href'] # Avoid static help pages
        ]

        # Remove duplicates
        course_links = list(set(course_links))

        if not course_links:
            print("❌ No courses found on the browse page.")
            return None

        print(f"✅ Found {len(course_links)} courses.")

        # 4. PICK ONE RANDOM COURSE
        random_path = random.choice(course_links)
        full_url = random_path if random_path.startswith("http") else f"{BASE_URL}{random_path}"
        
        print(f"🎲 Selected Random Course: {full_url}")

        # 5. Scrape the Details of that single course
        detail_response = session.get(full_url, timeout=30)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # Extract Title
        title = detail_soup.find("h1").get_text(strip=True) if detail_soup.find("h1") else "No Title Found"

        # Extract Content (Main body)
        # We look for the main content div (often class 'training-view' or id 'content')
        content_area = detail_soup.find("div", class_="training-view") or detail_soup.find("div", id="content") or detail_soup.body
        
        # Clean the text (remove excessive blank lines)
        raw_text = content_area.get_text(separator="\n", strip=True)
        
        # Structure the data
        course_data = {
            "title": title,
            "url": full_url,
            "full_text": raw_text[:5000] # Limit text length for AI
        }

        return course_data

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return None

if __name__ == "__main__":
    # 1. Scrape Data
    data = get_random_course()

    if data:
        # 2. Send to Make.com
        # REPLACE THIS URL WITH YOUR REAL MAKE WEBHOOK ADDRESS
        webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "https://hook.eu2.make.com/zkhfemycf3ghikg3rrsqtt6x2tnp2cxl")
        
        print("📤 Sending data to Make...")
        try:
            r = requests.post(webhook_url, json=data)
            print(f"✅ Data sent! Status Code: {r.status_code}")
            print("Response:", r.text)
        except Exception as e:
            print(f"❌ Failed to send webhook: {e}")
    else:
        print("⚠️ No data scraped.")