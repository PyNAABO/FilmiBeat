import cloudscraper
from bs4 import BeautifulSoup
import json
import logging
import requests

# ====== CONFIG ======
PANTRY_ID = "ffbc82fc-3471-4eb5-80bd-cf7cc6887fe1"  # <- REPLACE THIS
BASKET_NAME = "filmibeat"
URL = "https://www.filmibeat.com/top-listing/ott-movie-releases-this-week/?filter_type=releases"
OUTPUT_FILE = "ott_releases.json"
MAX_MOVIES = 25  # Change this to however many movies you want to keep

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
    if not text:
        return None, []
    parts = [part.strip() for part in text.split("|")]
    language = parts[0] if parts else None
    genres = parts[1:] if len(parts) > 1 else []
    return language, genres


def parse_movie_block(block):
    lang_genre_raw = get_text(
        block.select_one(".picture-detail p:nth-of-type(3)"))
    language, genres = parse_language_and_genre(lang_genre_raw)

    return {
        "title":
        get_text(block.select_one(".picture-detail p:nth-of-type(1)")),
        "type": get_text(block.select_one(".picture-detail p:nth-of-type(2)")),
        "language": language,
        "genres": genres,
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


def get_pantry_movies():
    url = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/{BASKET_NAME}"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            logging.warning(
                f"Failed to fetch pantry contents: {res.status_code}")
            return []
        return res.json()
    except Exception as err:
        logging.warning(f"Error fetching pantry data: {err}")
        return []


def overwrite_pantry(movies):
    url = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/{BASKET_NAME}"
    try:
        res = requests.put(url, json=movies)
        if res.status_code != 200:
            logging.warning(f"PantryDB update failed: {res.status_code}")
        else:
            logging.info(f"PantryDB updated with {len(movies)} movies")
    except Exception as err:
        logging.warning(f"PantryDB error: {err}")


# ====== SCRAPE HTML ======
try:
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL)

    if response.status_code != 200:
        logging.error(f"Failed to fetch page: {response.status_code}")
        raise SystemExit("Request failed")

    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logging.info("HTML saved to response.html")

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

# ====== GET PANTRY MOVIES ======
pantry_movies = get_pantry_movies()
pantry_titles = set(
    movie.get("title") for movie in pantry_movies if movie.get("title"))

# ====== ONLY ADD NEW MOVIES NOT IN PANTRY ======
scraped_new = [
    movie for movie in scraped if movie.get("title") not in pantry_titles
]

# ====== COMBINE AND DEDUPE ======
# Only include pantry movies and new scraped ones not yet processed
new_candidates = pantry_movies + scraped_new
deduped = dedupe_by_title(new_candidates)
final_movies = deduped[:MAX_MOVIES]

# ====== SAVE TO JSON & PANTRY ======
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_movies, f, indent=4, ensure_ascii=False)
    logging.info(f"{len(final_movies)} movies saved to {OUTPUT_FILE}")
except Exception as e:
    logging.exception("Failed to write ott_releases.json")
    raise SystemExit(e)

overwrite_pantry(final_movies)
