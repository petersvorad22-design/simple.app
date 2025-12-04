import json
from curl_cffi import requests
from bs4 import BeautifulSoup

def scrape_salto_course(search_text):
    # 1. SETUP: Mimic a real Chrome Browser to bypass security
    session = requests.Session(impersonate="chrome")
    browse_url = "https://www.salto-youth.net/tools/european-training-calendar/browse/"

    print(f"🔍 Searching for course matching: '{search_text}'...")

    try:
        # 2. FIND THE COURSE IN THE LIST
        response = session.get(browse_url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the link containing your specific text
        link_element = soup.find("a", string=lambda t: t and search_text in t)

        if not link_element:
            print("❌ No course found with that name.")
            return None

        # Get full URL
        href = link_element['href']
        full_url = href if href.startswith("http") else f"https://www.salto-youth.net{href}"
        
        print(f"✅ Found: {link_element.text.strip()}")
        print(f"🚀 Visiting: {full_url}")

        # 3. SCRAPE THE FULL DETAILS
        detail_response = session.get(full_url, timeout=15)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # Extract specific fields
        # Note: These selectors are standard for SALTO but may vary slightly by page layout
        title = detail_soup.find("h1").get_text(strip=True) if detail_soup.find("h1") else "No Title"
        
        # The main content usually lives in a specific div. We get all text to be safe.
        # We try to target the 'training-view' or main content area to avoid menus.
        content_area = detail_soup.find("div", class_="training-view") or detail_soup.find("div", id="content") or detail_soup.body
        full_text = content_area.get_text(separator="\n", strip=True)

        # 4. PREPARE DATA FOR MAKE / AI
        # We return a clean JSON object
        course_data = {
            "title": title,
            "url": full_url,
            "full_content": full_text[:4000] # Truncate to 4000 chars to fit AI context windows
        }

        return course_data

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # --- INPUT YOUR SEARCH TEXT HERE ---
    target_name = "Need Advice on Improving the Inclusion" 
    
    data = scrape_salto_course(target_name)
    
    if data:
        print("\n" + "="*30)
        print("COPY THE JSON BELOW FOR MAKE:")
        print("="*30)
        print(json.dumps(data, indent=4))