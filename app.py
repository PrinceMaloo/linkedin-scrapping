from flask import Flask, request, jsonify, send_file, render_template
from linkedin_scraper import Person
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()
LI_AT = os.getenv("LINKEDIN_LI_AT")

app = Flask(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com")
    driver.add_cookie({
        'name': 'li_at',
        'value': LI_AT,
        'domain': '.linkedin.com',
        'secure': True,
        'httpOnly': True,
    })
    return driver

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape_profile():
    data = request.json
    profile_url = data.get("url")

    if not profile_url:
        return jsonify({"error": "No URL provided"}), 400

    driver = get_driver()
    try:
        driver.get(profile_url)
        time.sleep(2)
        person = Person(profile_url, driver=driver)

        username = profile_url.strip("/").split("/")[-1]
        person_dict = {
            "name": person.name,
            "about": person.about,
            "experiences": [
                {
                    "institution_name": exp.institution_name,
                    "linkedin_url": exp.linkedin_url,
                    "position_title": exp.position_title,
                    "duration": exp.duration,
                    "location": exp.location,
                    "description": exp.description,
                    "from_date": exp.from_date,
                    "to_date": exp.to_date
                }
                for exp in person.experiences or []
            ],
            "educations": [
                {
                    "institution_name": edu.institution_name,
                    "linkedin_url": edu.linkedin_url,
                    "degree": edu.degree,
                    "from_date": edu.from_date,
                    "to_date": edu.to_date,
                    "description": edu.description
                }
                for edu in person.educations or []
            ],
            "interests": [i for i in person.interests or []],
            "accomplishments": [a for a in person.accomplishments or []],
            "contacts": [c for c in person.contacts or []],
        }

        file_path = f"{username}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(person_dict, f, indent=4, ensure_ascii=False)

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
