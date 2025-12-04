import requests
from bs4 import BeautifulSoup
import time

def get_training_details():
    # 1. THE SEARCH PAGE URL
    # Replace this with the actual URL where your list of cards is
    search_url = "https://www.salto-youth.net/tools/european-training-calendar/browse/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"1. Fetching search page...")
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to load search page.")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 2. FIND THE SPECIFIC CARD & LINK
    # We look for the <a> tag that contains your specific text
    target_text = "Need Advice on Improving the Inclusion"
    
    # This searches all links on the page for that specific text
    link_element = soup.find("a", string=lambda t: t and target_text in t)

    if link_element:
        # Extract the 'href' (the web address)
        relative_link = link_element['href']
        
        # Handle cases where the link is relative (e.g. "/tools/...") vs absolute
        if relative_link.startswith("http"):
            full_url = relative_link
        else:
            full_url = f"https://www.salto-youth.net{relative_link}"
            
        print(f"Found match: {link_element.text.strip()}")
        print(f"2. 'Clicking' link (visiting): {full_url}")
        
        # 3. VISIT THE NEW PAGE (The "Click" Action)
        details_response = requests.get(full_url, headers=headers)
        details_soup = BeautifulSoup(details_response.text, "html.parser")
        
        # 4. GET THE CLEAN CONTENT
        # We target the specific container for training details to avoid menu noise
        # usually inside a div with id 'content' or class 'training-view'
        content_div = details_soup.find("div", class_="training-view") or details_soup.find("div", id="content") or details_soup.body
        
        # Strip generic noise if needed
        full_text = content_div.get_text(separator="\n", strip=True)
        
        print("-" * 20)
        print("OUTPUT DATA FOR AI:")
        print("-" * 20)
        print(full_text)
        
        # Save to file so you can check it
        with open("final_output.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
            
    else:
        print(f"Could not find any link containing text: '{target_text}'")

if __name__ == "__main__":
    get_training_details()