import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime

# --- CONFIGURATION ---
# The URL where the list of courses is located
BASE_URL = "https://www.salto-youth.net"
CALENDAR_URL = "https://www.salto-youth.net/tools/european-training-calendar/search/"

def get_newest_course_link():
    """
    Fetches the main calendar page and finds the link to the top/newest course.
    """
    print("Checking for new courses...")
    try:
        response = requests.get(CALENDAR_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # NOTE: You must inspect the website to get the exact CSS selector.
        # This is a generic example assuming the first link in a table is the newest.
        # Look for the specific HTML class used for course titles on the site.
        # Example selector: 'table.training-list tr a.training-title'
        newest_link_tag = soup.select_one('.training-list-content a') 
        
        if newest_link_tag:
            link = newest_link_tag['href']
            # Ensure the link is absolute
            if not link.startswith("http"):
                link = BASE_URL + link
            return link
        else:
            print("No course links found.")
            return None
    except Exception as e:
        print(f"Error fetching list: {e}")
        return None

def scrape_course_details(url):
    """
    Visits the specific course page and extracts details.
    """
    print(f"Scraping details from: {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- EXTRACTION LOGIC ---
        # Adjust these selectors based on the actual HTML of the page
        
        # 1. Title
        title = soup.find('h1').get_text(strip=True)
        
        # 2. Description (Usually in a specific div)
        # We take the first 300 chars for the prompt to keep it concise
        description_div = soup.select_one('.content-text') # specific class needed
        description = description_div.get_text(strip=True)[:300] if description_div else "No description found."

        # 3. Dates/Location
        # Example: looking for a div with class 'training-date'
        date_info = soup.select_one('.date-display').get_text(strip=True) if soup.select_one('.date-display') else "Date unknown"
        
        return {
            "title": title,
            "description": description,
            "date": date_info,
            "url": url
        }
    except Exception as e:
        print(f"Error scraping details: {e}")
        return None

def generate_image_prompt(course_data):
    """
    Creates an image prompt based on the extracted text + your specific style preference.
    """
    title = course_data['title']
    desc_snippet = course_data['description']
    
    # --- PROMPT ENGINEERING ---
    # Integrating your "Bubble Style" preference with the course topic
    
    prompt = (
        f"Design a modern, 3D abstract illustration for a workshop titled '{title}'. "
        f"The theme involves: {desc_snippet}... "
        f"Key visual elements: Use a consistent style with floating semi-transparent bubbles, "
        f"soft gradients in blue and white, clean corporate memphis style, "
        f"high resolution, minimalist background."
    )
    
    return prompt

def job():
    """
    The main task to run daily.
    """
    print(f"--- Starting Job: {datetime.now()} ---")
    
    # 1. Get the link
    link = get_newest_course_link()
    
    if link:
        # 2. Get the details
        details = scrape_course_details(link)
        
        if details:
            # 3. Create the prompt
            image_prompt = generate_image_prompt(details)
            
            # 4. Output (In a real scenario, this could email you or save to a file)
            print("\n--- RESULTS ---")
            print(f"Course: {details['title']}")
            print(f"URL: {details['url']}")
            print(f"Generated Image Prompt:\n{image_prompt}")
            print("----------------")
            
            # Optional: Save to a log file
            with open("daily_course_log.txt", "a") as f:
                f.write(f"{datetime.now()} | {details['title']} | {image_prompt}\n")
                
    else:
        print("Could not find a link to process.")

# --- SCHEDULER ---
# Runs the 'job' function every day at 09:00 AM
schedule.every().day.at("09:00").do(job)

print("Scheduler started. Waiting for 09:00 AM... (Press Ctrl+C to stop)")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)