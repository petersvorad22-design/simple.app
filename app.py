import requests
from bs4 import BeautifulSoup
import time

def get_training_details_robust():
    # URL where the list of cards is located
    search_url = "https://www.salto-youth.net/tools/european-training-calendar/browse/"
    
    # Text you want to find (from your previous image)
    target_text = "Need Advice on Improving the Inclusion"

    # 1. SETUP SESSION (Stores cookies to look like a real user)
    session = requests.Session()
    
    # Use headers that look EXACTLY like a real Chrome browser
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })

    print(f"1. Fetching search page: {search_url} ...")
    
    try:
        # TIMEOUT ADDED: Waits 30 seconds before giving up
        response = session.get(search_url, timeout=30)
        response.raise_for_status() # Check for 404 or 500 errors
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. FIND THE LINK
        # Logic: Find any <a> tag containing the target text
        link_element = soup.find("a", string=lambda t: t and target_text in t)

        if not link_element:
            print(f"❌ Could not find link with text: '{target_text}'")
            # Debug: Print first 5 links found to see what's going on
            print("Did you mean one of these?")
            for l in soup.find_all("a", limit=5):
                print(f" - {l.text.strip()}")
            return

        # Extract URL
        relative_link = link_element['href']
        if relative_link.startswith("http"):
            full_url = relative_link
        else:
            full_url = f"https://www.salto-youth.net{relative_link}"
            
        print(f"✅ Found match: {link_element.text.strip()}")
        print(f"2. Visiting detail page: {full_url}")
        
        # 3. VISIT DETAIL PAGE (Simulating the 'Click')
        # We add a small random delay to be polite/human-like
        time.sleep(2) 
        
        detail_response = session.get(full_url, timeout=30)
        detail_response.raise_for_status()
        
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        
        # 4. EXTRACT CONTENT
        # Try to find the specific content div, fallback to body if not found
        content_area = detail_soup.find("div", class_="training-view") or detail_soup.body
        
        clean_text = content_area.get_text(separator="\n", strip=True)
        
        print("-" * 30)
        print("DATA EXTRACTED SUCCESSFULLY")
        print("-" * 30)
        print(clean_text[:500]) # Print first 500 chars as preview
        print("... (rest of file) ...")
        
        # Save to file
        with open("training_output.txt", "w", encoding="utf-8") as f:
            f.write(clean_text)
            
    except requests.exceptions.Timeout:
        print("❌ Error: The request timed out. The server took too long to respond.")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Connection failed. Check your internet or firewall.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    get_training_details_robust()