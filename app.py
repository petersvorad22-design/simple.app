from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random

app = Flask(__name__)

def scrape_course_by_id(course_id):
    # Try to build a URL with this ID
    # Structure seems to be: /eu/programme/{id}/eu (or similar country codes)
    url = f"https://programmes.eurodesk.eu/eu/programme/{course_id}/eu"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        # If the ID doesn't exist, Eurodesk might redirect or show 404
        if response.status_code != 200: 
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we actually found a valid page (look for the Title)
        title_tag = soup.find('div', class_='text-2xl font-bold uppercase')
        if not title_tag:
            return None # It was a 200 OK page but empty/error page
            
        title = title_tag.get_text(strip=True)
        
        # Grab Description
        content_div = soup.find('div', attrs={'data-role': 'body'})
        description, deadline = "", "See link"
        if content_div:
            description = content_div.get_text(separator='\n\n', strip=True)
            text_content = content_div.get_text()
            match = re.search(r'Deadlines?:(.*?)(?=\n|$)', text_content, re.IGNORECASE | re.DOTALL)
            if match:
                 deadline = match.group(1).strip()[:100]
        
        # Grab Image
        image_url = ""
        meta_image = soup.find("meta", property="og:image")
        if meta_image: image_url = meta_image["content"]
        if image_url and image_url.startswith('/'): 
            image_url = "https://programmes.eurodesk.eu" + image_url

        return {
            "title": title,
            "description": description[:3000],
            "deadline": deadline,
            "image": image_url,
            "link": url
        }
    except:
        return None

@app.route('/scrape_random', methods=['POST', 'GET'])
def scrape_random_course():
    # We will try up to 10 random IDs to find a winner
    attempts = 0
    max_attempts = 15
    
    # Based on current Eurodesk IDs (approx 20000 to 24000 are recent)
    min_id = 21000
    max_id = 24000
    
    while attempts < max_attempts:
        random_id = random.randint(min_id, max_id)
        result = scrape_course_by_id(random_id)
        
        if result:
            return jsonify({"status": "success", "attempts": attempts+1, "data": result})
        
        attempts += 1
        
    return jsonify({"error": "Could not find a valid course after multiple guesses"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)