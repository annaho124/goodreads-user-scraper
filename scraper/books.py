"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""

import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from argparse import Namespace
from scraper import author


def get_num_ratings(soup):

    num_ratings = soup.find("span", {"data-testid": "ratingsCount"}).text
    num_ratings = re.search(r"(.*)\s", num_ratings)[0].strip().replace(",", "")

    return int(num_ratings)


def get_num_reviews(soup):

    num_reviews = soup.find("span", {"data-testid": "reviewsCount"}).text
    num_reviews = re.search(r"(.*)\s", num_reviews)[0].strip().replace(",", "")

    return int(num_reviews)


def get_genres(soup):
    genres = []
    for node in soup.find_all(
        "span", {"class": "BookPageMetadataSection__genreButton"}
    ):
        current_genres = node.find_all(
            "a", {"class": "Button Button--tag-inline Button--small"}
        )
        current_genre = " > ".join([g.text for g in current_genres])
        if current_genre.strip():
            genres.append(current_genre)
    return genres


def get_series_name(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_name = re.search(r"\((.*?)\)", series.text).group(1)
        return series_name
    else:
        return None


def get_series_uri(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_uri = series.get("href")
        return "https://www.goodreads.com" + series_uri
    else:
        return None


def get_rating_distribution(soup):

    all_rating = soup.find_all("div", {"data-testid": re.compile(r"labelTotal")})
    distribution_dict = {}
    for rating in all_rating:

        rate = int(re.search(r"\d", rating.attrs.get("data-testid")).group())

        num_rating = int(re.search(r"(.*)\s", rating.text)[0].strip().replace(",", ""))

        distribution_dict[rate] = num_rating

    return distribution_dict


def get_num_pages(soup):
    if soup.find("span", {"itemprop": "numberOfPages"}):
        num_pages = soup.find("span", {"itemprop": "numberOfPages"}).text.strip()
        return int(num_pages.split()[0])
    return ""


def get_year_first_published(soup):
    year_first_published = soup.find("nobr", attrs={"class": "greyText"})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search("([0-9]{3,4})", year_first_published).group(1)
    else:
        return None


def get_author_id(soup):
    author_url = soup.find("a", {"class": "Avatar Avatar--large"}).attrs.get("href")
    return author_url.split("/")[-1]


def get_description(soup):
    return soup.find("div", {"data-testid": "description"}).findAll("span")[-1].text


def get_id(book_id):
    pattern = re.compile("([^.-]+)")
    return pattern.search(book_id).group()


def scrape_book(book_id: str, args: Namespace):
    url = "https://www.goodreads.com/book/show/" + book_id
    source = urlopen(url, timeout=60000)
    soup = BeautifulSoup(source, "html.parser")

    # print(book_id)

    book = {
        "book_id_title": book_id,
        "book_id": get_id(book_id),
        "book_title": " ".join(
            soup.find("h1", {"data-testid": "bookTitle"}).text.split()
        ),
        "book_description": get_description(soup),
        "book_url": url,
        "book_image": soup.find("img", {"class": "ResponsiveImage"}).attrs.get("src"),
        # "book_series": get_series_name(soup),
        # "book_series_uri": get_series_uri(soup),
        "year_first_published": get_year_first_published(soup),
        "num_pages": get_num_pages(soup),
        "genres": get_genres(soup),
        "num_ratings": get_num_ratings(soup),
        "num_reviews": get_num_reviews(soup),
        "average_rating": float(
            soup.find("div", {"class": "RatingStatistics__rating"}).text
        ),
        "rating_distribution": get_rating_distribution(soup),
    }

    if not args.skip_authors:
        book["author"] = author.scrape_author(get_author_id(soup))

    return book
