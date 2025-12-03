from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import random
import re

app = Flask(__name__)

# --- WORKER: Scrapes the details of ONE course ---
def get_salto_details(target_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. TITLE
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Title Not Found"

        # 2. DESCRIPTION & DEADLINE
        description = ""
        deadline = "See link"
        
        # SALTO specific content box
        content_area = soup.find('div', class_='training-view') 
        if not content_area: content_area = soup.find('table', class_='training_view') 

        if content_area:
            description = content_area.get_text(separator='\n\n', strip=True)
            
            # Find Deadline
            text_content = content_area.get_text()
            match = re.search(r'Application deadline\s*:?\s*(.*?)(?=\n|$)', text_content, re.IGNORECASE)
            if match:
                 deadline = match.group(1).strip()
        else:
             description = soup.get_text(separator='\n\n', strip=True)[:3000]

        # 3. IMAGE (SALTO usually doesn't have course images, so we use a default or logo)
        image_url = "https://www.salto-youth.net/images/salto-logo.png"

        return {
            "title": title,
            "description": description[:3500], 
            "deadline": deadline,
            "image": image_url,
            "link": target_url
        }
    except Exception as e:
        return None

# --- MANAGER: Finds the list and picks one ---
@app.route('/scrape_random', methods=['POST', 'GET'])
def scrape_random_course():
    try:
        # HERE IS THE LINK YOU GAVE ME:
        browse_url = "https://www.salto-youth.net/tools/european-training-calendar/browse/"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(browse_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links that go to a specific training
        all_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # We filter for links that look like "/training/course-name.1234/"
            if '/training/' in href and href.count('/') > 4: 
                full_url = href
                if not full_url.startswith('http'):
                    full_url = "https://www.salto-youth.net" + full_url
                all_links.append(full_url)
        
        all_links = list(set(all_links)) # Remove duplicates

        if not all_links:
            return jsonify({"error": "No trainings found on the SALTO browse page"}), 404

        # Pick one random link from the list
        selected_url = random.choice(all_links)
        
        # Scrape it
        data = get_salto_details(selected_url)
        
        if data:
             return jsonify({"status": "success", "data": data})
        else:
             return jsonify({"error": "Failed to scrape the selected course"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)