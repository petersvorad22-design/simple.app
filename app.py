from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape_eurodesk():
    data = request.json
    target_url = data.get('url')
    
    if not target_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # 1. Fake a browser (Standard headers)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(target_url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({"error": f"Failed to load page: {response.status_code}"}), 400

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- INTELLIGENT PARSING ---

        # A. TITLE
        # We look for the bold uppercase title class you found earlier
        title_tag = soup.find('div', class_='text-2xl font-bold uppercase')
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Title Not Found"

        # B. DESCRIPTION & BODY
        # We target the specific container you found: <div data-role="body">
        content_div = soup.find('div', attrs={'data-role': 'body'})
        
        description = ""
        deadline = "See link for details"

        if content_div:
            # 1. Get clean text for the AI (preserves paragraph breaks)
            # separator='\n\n' makes sure paragraphs don't get mushed together
            description = content_div.get_text(separator='\n\n', strip=True)

            # 2. Extract Deadline specifically (Logic: Look for "Deadlines:" inside this body)
            # We look for the text pattern "Deadlines:" and grab the text immediately after
            text_content = content_div.get_text()
            match = re.search(r'Deadlines?:(.*?)(?=\n|$)', text_content, re.IGNORECASE | re.DOTALL)
            if match:
                # Grab the first 100 chars after "Deadline:" to catch dates like "1 December 2023"
                potential_date = match.group(1).strip()
                if len(potential_date) < 5: # If it found nothing on that line, look ahead
                     deadline = text_content[match.end():match.end()+100].strip()
                else:
                    deadline = potential_date[:100]

        else:
            # Fallback if structure changes
            description = "Could not locate main body text."

        # C. IMAGE
        # Priority 1: Open Graph Meta Tag (Best for social media)
        image_url = ""
        meta_image = soup.find("meta", property="og:image")
        if meta_image:
            image_url = meta_image["content"]
        
        # Priority 2: If no meta image, look for an image INSIDE the content body
        if not image_url and content_div:
            body_img = content_div.find('img')
            if body_img and 'src' in body_img.attrs:
                image_url = body_img['src']
                if image_url.startswith('/'): # Fix relative links
                    image_url = "https://programmes.eurodesk.eu" + image_url

        # D. Return Data to Make.com
        return jsonify({
            "status": "success",
            "data": {
                "title": title,
                "description": description[:3000], # Send first 3000 chars to AI to save tokens
                "deadline": deadline,
                "image": image_url,
                "link": target_url
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)