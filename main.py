import cloudscraper
from bs4 import BeautifulSoup
import json
import logging
import requests

# ====== CONFIG ======
PANTRY_ID = "ffbc82fc-3471-4eb5-80bd-cf7cc6887fe1"
FILMIBEAT_BASKET = "filmibeat"
DONE_BASKET = "done"
URL = "https://www.filmibeat.com/top-listing/ott-movie-releases-this-week/?filter_type=releases"
OUTPUT_FILE = "ott_releases.json"
MAX_MOVIES = 25  # Max number of movies to keep

# ====== LOGGING ======
logging.basicConfig(filename="scraper.log",
                    level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logging.info("Starting scraper")


# ====== UTILS ======
def get_text(selector):
    return selector.text.strip() if selector else None


def get_src(tag):
    return tag['src'] if tag and tag.has_attr('src') else None


def parse_language_and_genre(text):
    return text.strip(
    ) if text else None  # Keep as single string like "bn | Drama"


def parse_movie_block(block):
    lang_genre_raw = get_text(
        block.select_one(".picture-detail p:nth-of-type(3)"))

    return {
        "title":
        get_text(block.select_one(".picture-detail p:nth-of-type(1)")),
        "type": get_text(block.select_one(".picture-detail p:nth-of-type(2)")),
        "language_genre": parse_language_and_genre(lang_genre_raw),
        "release_date": get_text(block.select_one(".release-date p")),
        "ott_platform": get_text(block.select_one(".OTT-platform p")),
        "poster_url": get_src(block.select_one(".movie-image img")),
    }


def dedupe_by_title(movies):
    seen = set()
    unique = []
    for movie in movies:
        title = movie.get("title")
        if title and title not in seen:
            seen.add(title)
            unique.append(movie)
    return unique


def get_pantry_movies(basket_name):
    url = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/{basket_name}"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            logging.warning(
                f"Failed to fetch basket {basket_name}: {res.status_code}")
            return []
        data = res.json()
        return data.get("Movies", []) if isinstance(data, dict) else []
    except Exception as err:
        logging.warning(f"Error fetching pantry basket {basket_name}: {err}")
        return []


def overwrite_pantry(basket_name, movies):
    url = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/{basket_name}"
    payload = {"Movies": movies}
    try:
        res = requests.put(url, json=payload)
        if res.status_code != 200:
            logging.warning(
                f"Failed to update basket {basket_name}: {res.status_code}")
        else:
            logging.info(
                f"{basket_name} basket updated with {len(movies)} movies")
    except Exception as err:
        logging.warning(f"Error updating pantry basket {basket_name}: {err}")


# ====== SCRAPE HTML ======
try:
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL)

    if response.status_code != 200:
        logging.error(f"Failed to fetch page: {response.status_code}")
        raise SystemExit("Request failed")

except Exception as e:
    logging.exception("Error during scraping")
    raise SystemExit(e)

# ====== PARSE MOVIES ======
soup = BeautifulSoup(response.text, 'html.parser')
scraped = []

for i, block in enumerate(soup.select("div.list-content")):
    try:
        movie = parse_movie_block(block)
        if movie["title"]:
            scraped.append(movie)
            logging.info(f"Parsed movie #{i+1}: {movie['title']}")
    except Exception as err:
        logging.warning(f"Failed to parse block #{i+1}: {err}")

scraped = dedupe_by_title(scraped)

# ====== GET DONE MOVIES ======
done_movies = get_pantry_movies(DONE_BASKET)
done_titles = set(m.get("title") for m in done_movies if m.get("title"))

# ====== FILTER SCRAPED ======
filtered = [m for m in scraped if m.get("title") not in done_titles]
final_movies = filtered[:MAX_MOVIES]

# ====== SAVE TO JSON & PANTRY ======
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"Movies": final_movies}, f, indent=4, ensure_ascii=False)
    logging.info(f"{len(final_movies)} movies written to {OUTPUT_FILE}")
except Exception as e:
    logging.exception("Failed to write ott_releases.json")
    raise SystemExit(e)

overwrite_pantry(FILMIBEAT_BASKET, final_movies)
