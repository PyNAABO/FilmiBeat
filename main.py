from bs4 import BeautifulSoup
import cloudscraper
import json

url = "https://www.filmibeat.com/top-listing/ott-movie-releases-this-week/?filter_type=releases"

scraper = cloudscraper.create_scraper()
response = scraper.get(url)

# Optional: Save the HTML for debugging
with open("response.html", "w", encoding="utf-8") as f:
    f.write(response.text)

soup = BeautifulSoup(response.text, 'html.parser')

movies = []

for block in soup.select("div.movie-list"):
    title = block.select_one(".movie-list__detail p:nth-of-type(1)")
    date_type = block.select_one(".movie-list__detail p:nth-of-type(2)")
    lang_genre = block.select_one(".movie-list__detail p:nth-of-type(3)")
    ott_platform = block.select_one(".OTT-platform p")
    poster = block.select_one(".movie-list_image img")

    # Split date_type
    if date_type and '|' in date_type.text:
        release_date, content_type = map(str.strip,
                                         date_type.text.strip().split('|', 1))
    else:
        release_date = content_type = None

    movie_data = {
        "title": title.text.strip() if title else None,
        "type": content_type,
        "language_genre": lang_genre.text.strip() if lang_genre else None,
        "release_date": release_date,
        "ott_platform": ott_platform.text.strip() if ott_platform else None,
        "poster_url":
        poster['src'] if poster and poster.has_attr('src') else None
    }

    movies.append(movie_data)

# Save to JSON
with open("ott_releases.json", "w", encoding="utf-8") as f:
    json.dump(movies, f, indent=4, ensure_ascii=False)

print(f"{len(movies)} movies scraped and saved.")
