import random
from flask import Flask, jsonify
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_URL = "https://www.salto-youth.net"
BROWSE_URL = "https://www.salto-youth.net/tools/european-training-calendar/browse/"

def clean_dom(soup):
    """
    Surgically removes headers, footers, sidebars, and menus 
    so only the main content remains.
    """
    # List of "Noise" classes usually found on SALTO (Sidebars, Menus, Footers)
    noise_selectors = [
        ".region-sidebar-first",  # The left sidebar (About SALTO, etc.)
        ".region-sidebar-second", # Right sidebar
        "#footer",                # The bottom footer
        ".utility-menu",          # Top menu
        ".branding",              # Logo area
        ".tabs",                  # "View / Edit" tabs
        ".breadcrumb"             # Navigation path
    ]
    
    # Destroy them!
    for selector in noise_selectors:
        for element in soup.select(selector):
            element.decompose() # This deletes the element from the HTML completely
            
    return soup

def get_random_course_data():
    session = cffi_requests.Session(impersonate="chrome")
    
    try:
        # 1. Get List of Courses
        print("🔍 Scanning course list...")
        response = session.get(BROWSE_URL, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all valid course links
        all_links = soup.find_all("a", href=True)
        course_links = [
            link['href'] for link in all_links 
            if "/tools/european-training-calendar/training/" in link['href'] 
            and "apply" not in link['href'] 
            and ".html" not in link['href']
        ]

        if not course_links:
            return {"error": "No courses found"}

        # 2. Pick ONE Random Course
        random_path = random.choice(course_links)
        full_url = random_path if random_path.startswith("http") else f"{BASE_URL}{random_path}"
        print(f"🎲 Selected: {full_url}")

        # 3. Scrape Details
        detail_response = session.get(full_url, timeout=30)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # --- NEW: RUN THE CLEANER ---
        detail_soup = clean_dom(detail_soup)

        # Extract Title
        title = detail_soup.find("h1").get_text(strip=True) if detail_soup.find("h1") else "No Title"
        
        # Extract Main Content
        # We target the specific content box 'training-view'. 
        # If not found, we use 'content' ID but the noise is already deleted by clean_dom
        content_area = detail_soup.find("div", class_="training-view") or detail_soup.find("div", id="content") or detail_soup.body
        
        full_text = content_area.get_text(separator="\n", strip=True)

        # 4. FINAL SAFETY CUT
        # If "About SALTO" still survives, we cut everything after it using text splitting
        if "About SALTO" in full_text:
            full_text = full_text.split("About SALTO")[0]

        return {
            "title": title,
            "url": full_url,
            "full_text": full_text[:4000] # Limit text size for AI
        }

    except Exception as e:
        return {"error": str(e)}

# --- WEB SERVER ROUTES ---
@app.route('/')
def home():
    return "✅ Scraper is Alive (Clean Version). Go to /scrape"

@app.route('/scrape')
def scrape():
    data = get_random_course_data()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)