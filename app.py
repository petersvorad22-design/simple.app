import requests
from bs4 import BeautifulSoup
import time

# --- CONFIGURATION ---
BASE_URL = "https://www.salto-youth.net"
# This is the page that lists all current trainings
LIST_URL = "https://www.salto-youth.net/tools/european-training-calendar/browse/"

# Headers make the script look like a real Chrome browser to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def find_newest_course():
    print(f"1. Accessing calendar list: {LIST_URL}")
    try:
        response = requests.get(LIST_URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # SMART SEARCH: Find the first link that looks like a training course
        # We look for 'a' tags where the href contains '/training/' but isn't a search link
        all_links = soup.find_all('a', href=True)
        
        course_link = None
        for link in all_links:
            href = link['href']
            # Filter for actual training pages (avoiding admin/search links)
            if "/tools/european-training-calendar/training/" in href and "search" not in href:
                course_link = href
                if not course_link.startswith("http"):
                    course_link = BASE_URL + course_link
                break # We take the first one found (usually the top of the list)

        if course_link:
            print(f"   Found newest course link: {course_link}")
            return course_link
        else:
            print("   ❌ No training links found on the browse page.")
            return None

    except Exception as e:
        print(f"   Error fetching list: {e}")
        return None

def get_course_details(url):
    print(f"2. Scraping details from: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Get Title (H1 is usually the main title)
        title = soup.find('h1').get_text(strip=True)
        
        # 2. Get Description
        # We grab all paragraph text to be safe, then limit it to 300 chars
        all_text = soup.find_all('p')
        description = " ".join([p.get_text(strip=True) for p in all_text])
        # Clean up and shorten
        short_desc = description[:400] + "..." if len(description) > 400 else description

        return {"title": title, "description": short_desc, "url": url}

    except Exception as e:
        print(f"   Error reading page details: {e}")
        return None

def generate_prompt(data):
    print("3. Generating Image Prompt...")
    # Your Saved Preference: Bubble Style
    prompt = (
        f"**IMAGE PROMPT:**\n"
        f"Design a modern, 3D abstract illustration for a European training course titled '{data['title']}'. "
        f"Context of the event: {data['description']}\n\n"
        f"**Style Requirements:**\n"
        f"Use floating semi-transparent bubbles, soft gradients in blue and white, "
        f"clean corporate memphis style, high resolution, minimalist background."
    )
    return prompt

# --- MAIN EXECUTION (RUNS ONCE IMMEDIATELY) ---
if __name__ == "__main__":
    link = find_newest_course()
    
    if link:
        details = get_course_details(link)
        if details:
            final_prompt = generate_prompt(details)
            print("\n" + "="*40)
            print("SUCCESS! HERE IS YOUR DATA:")
            print("="*40)
            print(f"Title: {details['title']}")
            print(f"Link:  {details['url']}")
            print("-" * 20)
            print(final_prompt)
            print("="*40)
    else:
        print("Scraping failed.")