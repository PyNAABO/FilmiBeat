import cloudscraper
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Starting scraper")

url = "https://www.filmibeat.com/top-listing/ott-movie-releases-this-week/?filter_type=releases"

try:
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)

    if response.status_code != 200:
        logging.error(f"Failed to fetch page: {response.status_code}")
        raise SystemExit("Request failed")

    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logging.info("HTML saved to response.html")

except Exception as e:
    logging.exception("Error during scraping")
    raise SystemExit(e)

soup = BeautifulSoup(response.text, 'html.parser')
movies = []

for i, block in enumerate(soup.select("div.list-content")):
    try:
        title = block.select_one(".picture-detail p:nth-of-type(1)")
        content_type = block.select_one(".picture-detail p:nth-of-type(2)")
        lang_genre = block.select_one(".picture-detail p:nth-of-type(3)")
        release_date = block.select_one(".release-date p")
        ott_platform = block.select_one(".OTT-platform p")
        poster = block.select_one(".movie-image img")

        movie_data = {
            "title": title.text.strip() if title else None,
            "type": content_type.text.strip() if content_type else None,
            "language_genre": lang_genre.text.strip() if lang_genre else None,
            "release_date": release_date.text.strip() if release_date else None,
            "ott_platform": ott_platform.text.strip() if ott_platform else None,
            "poster_url": poster['src'] if poster and poster.has_attr('src') else None
        }

        logging.info(f"Parsed movie #{i+1}: {movie_data['title']}")
        movies.append(movie_data)

    except Exception as parse_err:
        logging.warning(f"Failed to parse movie block #{i+1}: {parse_err}")

try:
    with open("ott_releases.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=4, ensure_ascii=False)
    logging.info(f"{len(movies)} movies saved to ott_releases.json")
except Exception as write_err:
    logging.exception("Error writing JSON output")
    raise SystemExit(write_err)
