import cloudscraper
from bs4 import BeautifulSoup
import json

url = "https://www.filmibeat.com/top-listing/ott-movie-releases-this-week/?filter_type=releases"

# Create a Cloudflare-bypassing session
scraper = cloudscraper.create_scraper()  # This is like requests, but trickier
response = scraper.get(url)

# Save the raw HTML to inspect
with open("response.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("HTML saved to response.html")

# Parse with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

movies = []

for block in soup.select("div.list-content"):
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

    movies.append(movie_data)

# Save results to JSON
with open("ott_releases.json", "w", encoding="utf-8") as f:
    json.dump(movies, f, indent=4, ensure_ascii=False)

print(f"{len(movies)} movies saved to ott_releases.json")
