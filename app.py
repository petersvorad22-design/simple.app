from flask import Flask, jsonify
import random
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_URL = "https://www.salto-youth.net"
BROWSE_URL = "https://www.salto-youth.net/tools/european-training-calendar/browse/"

def run_scraper():
    print("🚀 Starting Scraper...")
    session = cffi_requests.Session(impersonate="chrome")

    try:
        # 1. Get the list of courses
        response = session.get(BROWSE_URL, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        # 2. Find links
        all_links = soup.find_all("a", href=True)
        course_links = [
            link['href'] for link in all_links 
            if "/tools/european-training-calendar/training/" in link['href'] 
            and "apply" not in link['href'] 
            and ".html" not in link['href']
        ]

        if not course_links:
            return {"error": "No courses found"}

        # 3. Pick Random Course
        random_path = random.choice(course_links)
        full_url = random_path if random_path.startswith("http") else f"{BASE_URL}{random_path}"
        
        # 4. Scrape Details
        detail_response = session.get(full_url, timeout=30)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        title = detail_soup.find("h1").get_text(strip=True) if detail_soup.find("h1") else "No Title"
        
        content_area = detail_soup.find("div", class_="training-view") or detail_soup.find("div", id="content") or detail_soup.body
        raw_text = content_area.get_text(separator="\n", strip=True)

        return {
            "title": title,
            "url": full_url,
            "full_text": raw_text[:4000] # Limit for AI
        }

    except Exception as e:
        return {"error": str(e)}

# --- THE WEB SERVER PART ---
@app.route('/')
def home():
    return "I am alive! Go to /scrape to run the bot."

@app.route('/scrape')
def scrape_endpoint():
    # This runs when Make.com visits https://your-app.onrender.com/scrape
    data = run_scraper()
    return jsonify(data)

if __name__ == "__main__":
    # This allows you to run it locally for testing
    app.run(host='0.0.0.0', port=10000)