from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import random
import re

app = Flask(__name__)

def get_salto_details(target_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. TITLE (Usually in an h1 tag)
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Title Not Found"

        # 2. DESCRIPTION & DEADLINE (SALTO uses tables)
        # We look for the main content table
        description = ""
        deadline = "See link"
        
        # SALTO puts info in table rows. We'll grab all text to be safe.
        # Find the specific row for "Description" if possible, or just grab the whole page text cleanly.
        content_area = soup.find('div', class_='training-view') # Common container
        
        if not content_area:
            # Fallback: Just look for the table
            content_area = soup.find('table', class_='training_view') 

        if content_area:
            description = content_area.get_text(separator='\n\n', strip=True)
            
            # Refine Description: Try to remove the "header" labels to make it cleaner
            # (Optional refinement, but raw text is usually fine for AI)

            # Find Deadline specifically
            # It is usually labelled "Application deadline"
            text_content = content_area.get_text()
            match = re.search(r'Application deadline\s*:?\s*(.*?)(?=\n|$)', text_content, re.IGNORECASE)
            if match:
                 deadline = match.group(1).strip()
        else:
             # Last resort fallback
             description = soup.get_text(separator='\n\n', strip=True)[:3000]

        # 3. IMAGE
        # SALTO rarely has specific images for courses, so we use the logo or look for one
        image_url = "https://www.salto-youth.net/images/salto-logo.png" # Default fallback
        
        # Try to find a real image inside the content
        if content_area:
            img_tag = content_area.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
                if image_url.startswith('/'):
                    image_url = "https://www.salto-youth.net" + image_url

        return {
            "title": title,
            "description": description[:3500], # Limit for AI
            "deadline": deadline,
            "image": image_url,
            "link": target_url
        }
    except Exception as e:
        print(f"Error details: {e}")
        return None

@app.route('/scrape_random', methods=['POST', 'GET'])
def scrape_random_course():
    try:
        # 1. Go to the Browse Page (List of all open calls)
        browse_url = "https://www.salto-youth.net/tools/european-training-calendar/browse/"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(browse_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"error": "Could not access SALTO browse page"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')

        # 2. Find all course links
        # SALTO links look like: /tools/european-training-calendar/training/name.1234/
        all_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/training/' in href and href.count('/') > 4: # Crude check to ensure it's a specific training, not a category
                full_url = href
                if not full_url.startswith('http'):
                    full_url = "https://www.salto-youth.net" + full_url
                all_links.append(full_url)
        
        # Remove duplicates
        all_links = list(set(all_links))

        if not all_links:
            return jsonify({"error": "No trainings found on browse page"}), 404

        # 3. Pick Random & Scrape
        # Try up to 3 times in case one is a dead link
        for _ in range(3):
            selected_url = random.choice(all_links)
            data = get_salto_details(selected_url)
            if data:
                 return jsonify({"status": "success", "data": data})

        return jsonify({"error": "Failed to scrape a valid course"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)