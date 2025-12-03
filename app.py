from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random
import xml.etree.ElementTree as ET

app = Flask(__name__)

# --- Helper: Scrape One Course ---
def get_course_details(target_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')

        # Title
        title_tag = soup.find('div', class_='text-2xl font-bold uppercase')
        title = title_tag.get_text(strip=True) if title_tag else (soup.find('h1').get_text(strip=True) if soup.find('h1') else "Title Not Found")

        # Body
        content_div = soup.find('div', attrs={'data-role': 'body'})
        description, deadline = "", "See link"
        if content_div:
            description = content_div.get_text(separator='\n\n', strip=True)
            text_content = content_div.get_text()
            match = re.search(r'Deadlines?:(.*?)(?=\n|$)', text_content, re.IGNORECASE | re.DOTALL)
            if match:
                 deadline = match.group(1).strip()[:100]
        else:
            description = "Could not locate body."

        # Image
        image_url = ""
        meta_image = soup.find("meta", property="og:image")
        if meta_image: image_url = meta_image["content"]
        if image_url and image_url.startswith('/'): image_url = "https://programmes.eurodesk.eu" + image_url

        return {
            "title": title,
            "description": description[:3000],
            "deadline": deadline,
            "image": image_url,
            "link": target_url
        }
    except Exception as e:
        print(f"Error scraping course: {e}")
        return None

# --- Main Endpoint: Use Sitemap to find links ---
@app.route('/scrape_random', methods=['POST'])
def scrape_random_course():
    try:
        # 1. We check the Eurodesk Sitemap (The master map of all pages)
        sitemap_url = "https://programmes.eurodesk.eu/sitemap.xml"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
             return jsonify({"error": "Could not access sitemap"}), 500

        # 2. Parse the XML to find links
        # The sitemap structure usually has <loc> tags inside <url> tags
        root = ET.fromstring(response.content)
        
        # XML namespaces can be tricky, so we ignore them by searching for all tags ending in 'loc'
        all_urls = []
        for elem in root.iter():
            if elem.tag.endswith('loc') and elem.text:
                url = elem.text
                # Filter: Only keep URLs that are actual programmes
                if "/programme/" in url:
                    all_urls.append(url)

        if not all_urls:
            return jsonify({"error": "No programme links found in sitemap"}), 404

        # 3. Pick ONE random link
        selected_url = random.choice(all_urls)

        # 4. Scrape it
        result = get_course_details(selected_url)
        
        if result:
             return jsonify({"status": "success", "data": result})
        else:
             # If the first random one failed (maybe expired), try one more time
             second_try = random.choice(all_urls)
             result_2 = get_course_details(second_try)
             if result_2:
                 return jsonify({"status": "success", "data": result_2})
             else:
                 return jsonify({"error": "Failed to scrape random course"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)