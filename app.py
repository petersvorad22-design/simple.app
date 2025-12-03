from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random
import urllib.parse

app = Flask(__name__)

def get_course_details(target_url):
    """
    This is the worker function that scrapes a specific page.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(target_url, headers=headers)
    
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # A. TITLE
    title_tag = soup.find('div', class_='text-2xl font-bold uppercase')
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Title Not Found"

    # B. DESCRIPTION
    content_div = soup.find('div', attrs={'data-role': 'body'})
    description = ""
    deadline = "See link for details"

    if content_div:
        description = content_div.get_text(separator='\n\n', strip=True)
        # Extract Deadline
        text_content = content_div.get_text()
        match = re.search(r'Deadlines?:(.*?)(?=\n|$)', text_content, re.IGNORECASE | re.DOTALL)
        if match:
            potential_date = match.group(1).strip()
            if len(potential_date) < 5: 
                 deadline = text_content[match.end():match.end()+100].strip()
            else:
                deadline = potential_date[:100]
    else:
        description = "Could not locate main body text."

    # C. IMAGE
    image_url = ""
    meta_image = soup.find("meta", property="og:image")
    if meta_image:
        image_url = meta_image["content"]
    
    # Fix relative image URLs
    if image_url and image_url.startswith('/'):
        image_url = "https://programmes.eurodesk.eu" + image_url

    return {
        "title": title,
        "description": description[:3000],
        "deadline": deadline,
        "image": image_url,
        "link": target_url
    }

@app.route('/scrape_random', methods=['POST', 'GET'])
def scrape_random_course():
    try:
        # 1. Go to the Main List to find links
        base_url = "https://programmes.eurodesk.eu"
        list_url = "https://programmes.eurodesk.eu/learning"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(list_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Find all links that look like a course (contain "/programme/")
        all_links = soup.find_all('a', href=True)
        course_links = []
        
        for link in all_links:
            href = link['href']
            if "/programme/" in href and "learning" not in href: # Avoid finding the list page itself
                full_url = urllib.parse.urljoin(base_url, href)
                course_links.append(full_url)
        
        # Remove duplicates
        course_links = list(set(course_links))

        if not course_links:
            return jsonify({"error": "No courses found on the main page"}), 404

        # 3. Pick ONE random link
        selected_url = random.choice(course_links)

        # 4. Scrape that specific link
        data = get_course_details(selected_url)
        
        if data:
             return jsonify({"status": "success", "data": data})
        else:
             return jsonify({"error": "Failed to scrape the selected course"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)