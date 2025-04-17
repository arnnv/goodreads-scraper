import argparse
import requests
from bs4 import BeautifulSoup
import time
import json
import logging
import sys
import urllib.parse
import os # Import os module

# --- Configuration ---
DEFAULT_BOOK_NAME = "The Final Empire"
BASE_URL = "https://www.goodreads.com"
SEARCH_URL = "https://www.goodreads.com/search?q={query}"
REQUEST_TIMEOUT = 15 # Seconds
POLITE_DELAY = 0.5 # Seconds between requests
MAX_REVIEWS_TO_SCRAPE = 3

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# --- Headers for Requests ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

# --- Helper Functions ---

def get_book_url(query):
    """Searches Goodreads and returns the URL of the first book result."""
    search_query = urllib.parse.quote_plus(query)
    url = SEARCH_URL.format(query=search_query)
    logging.info(f"Searching for: '{query}' at {url}")

    time.sleep(POLITE_DELAY)
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Search request failed for {url}: {e}")
        return None

    try:
        soup = BeautifulSoup(response.text, 'lxml') # Use lxml parser
        book_link_tag = soup.find('a', class_='bookTitle')

        if book_link_tag and book_link_tag.get('href'):
            book_path = book_link_tag['href']
            if book_path.startswith('/book/show'):
                book_url = BASE_URL + book_path.split('?')[0] # Clean URL
                logging.info(f"Found book link: {book_url}")
                return book_url
            else:
                logging.warning(f"Found link, but not a book path: {book_path}")
                return None
        else:
            logging.warning(f"Could not find book title link for query: '{query}'")
            return None
    except Exception as e:
        logging.error(f"Error parsing search results for '{query}': {e}")
        return None

def parse_reviews(html_content):
    """Parses HTML to extract up to MAX_REVIEWS_TO_SCRAPE reviews."""
    soup = BeautifulSoup(html_content, 'lxml')
    review_cards = soup.find_all('article', class_='ReviewCard')
    reviews = []

    if not review_cards:
        logging.warning("No review cards found ('article.ReviewCard'). Might be JS-loaded.")
        return reviews

    logging.info(f"Found {len(review_cards)} potential review cards in HTML.")

    for card in review_cards:
        if len(reviews) >= MAX_REVIEWS_TO_SCRAPE:
            logging.info(f"Reached review limit ({MAX_REVIEWS_TO_SCRAPE}). Stopping review parsing.")
            break

        reviewer_name_element = card.find('div', class_='ReviewerProfile__name')
        reviewer_name = reviewer_name_element.a.text.strip() if reviewer_name_element and reviewer_name_element.a else "Unknown User"

        review_text = "Review text not found." # Default
        review_body_element = card.find('section', class_='ReviewText__content')
        if review_body_element:
            review_text_element = review_body_element.find('span', class_='Formatted')
            if review_text_element:
                # Use get_text with a separator to preserve spaces between tags
                review_text = review_text_element.get_text(separator=' ').strip()
            else: # Basic fallback
                # Also apply to the fallback case
                review_text = review_body_element.get_text(separator=' ').strip()

            # Replace double spaces with single spaces
            review_text = review_text.replace('  ', ' ')
            # Remove literal '["br"]>' strings
            review_text = review_text.replace('["br"]>', '')

            if not review_text:
                review_text = "No review text found in structure."

        reviews.append({
            'reviewer_name': reviewer_name,
            'review_text': review_text
        })

    return reviews

def scrape_data(book_url):
    """Scrapes book info from its Goodreads page. Relies on static HTML content."""
    logging.info(f"Scraping book data from: {book_url}")

    time.sleep(POLITE_DELAY)
    try:
        response = requests.get(book_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch book page {book_url}: {e}")
        return None

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        book_data = {'url': book_url}

        # Title
        title_tag = soup.find('h1', class_="Text Text__title1", attrs={'data-testid': 'bookTitle'})
        book_data['title'] = title_tag.text.strip() if title_tag else 'N/A'

        # Author
        author_tag = soup.find('span', class_="ContributorLink__name")
        book_data['author'] = author_tag.text.strip() if author_tag else 'N/A'

        # Rating
        rating_tag = soup.find('div', class_='RatingStatistics__rating')
        try:
            book_data['rating'] = float(rating_tag.text.strip()) if rating_tag else 'N/A'
        except (ValueError, AttributeError):
            book_data['rating'] = 'N/A'

        # Review Count
        reviews_count_tag = soup.find('span', {"data-testid":"reviewsCount"})
        try:
            count_text = reviews_count_tag.text.strip().split()[0].replace(',', '')
            book_data['review_count'] = int(count_text) if reviews_count_tag and count_text.isdigit() else 'N/A'
        except (AttributeError, IndexError, ValueError):
            book_data['review_count'] = 'N/A'

        # Description
        description_container = soup.find('div', class_='BookPageMetadataSection__description')
        if description_container:
            description_tag = description_container.find('span', class_="Formatted")
        # Use get_text with separator for description
        description_text = description_tag.get_text(separator=' ').strip() if description_tag else 'N/A'
        # Replace double spaces with single spaces
        book_data['description'] = description_text.replace('  ', ' ')

        # Genres (All)
        genres = []
        genre_container = soup.find('div', class_="BookPageMetadataSection__genres")
        if genre_container:
            genre_items = genre_container.find_all('span', class_='BookPageMetadataSection__genreButton')
            for item in genre_items:
                genre_link = item.find('a')
                if genre_link:
                    genre_span = genre_link.find('span', class_="Button__labelItem")
                    if genre_span:
                        genre_text = genre_span.text.strip()
                        if genre_text:
                                genres.append(genre_text)
        book_data['genres'] = genres if genres else [] # Ensure it's a list

        # Reviews (Limited)
        book_data['reviews'] = parse_reviews(html_content)

        # Log summary
        logging.info(f"Extracted Title: {book_data['title']}")
        logging.info(f"Extracted Author: {book_data['author']}")
        logging.info(f"Extracted Rating: {book_data['rating']}")
        logging.info(f"Extracted Review Count: {book_data['review_count']}")
        logging.info(f"Extracted {len(book_data['genres'])} Genres: {book_data['genres']}")
        logging.info(f"Extracted {len(book_data['reviews'])} Reviews (max {MAX_REVIEWS_TO_SCRAPE})")

        return book_data

    except Exception as e:
        logging.error(f"Error scraping details for '{book_url}': {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

def save_data_json(data, filename_base):
    """Saves the scraped data to a JSON file inside the 'parsed_data' directory."""
    if not data:
        logging.warning("No data to save.")
        return

    output_dir = "parsed_data"
    json_filename = f"{filename_base}_goodreads_data.json"
    json_filepath = os.path.join(output_dir, json_filename)

    try:
        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Data successfully saved to {json_filepath}") # Use full path in log
    except IOError as e:
        logging.error(f"Failed to save data to JSON file {json_filepath}: {e}") # Use full path in log
    except Exception as e:
        logging.error(f"An unexpected error occurred during JSON saving: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape basic book data and limited reviews from Goodreads using requests.")
    parser.add_argument("-b", "--book", type=str, default=DEFAULT_BOOK_NAME,
                        help=f"Name of the book to search for (default: '{DEFAULT_BOOK_NAME}')")

    args = parser.parse_args()
    book_name = args.book
    filename_base = book_name.lower().replace(' ', '_').replace(':', '').replace('\'', '').replace('/', '').replace('\\', '')[:50]

    logging.info(f"--- Starting Goodreads Scraper for: {book_name} ---")
    logging.info(f"--- Using requests (max {MAX_REVIEWS_TO_SCRAPE} reviews, JSON output only) ---")

    try:
        book_url = get_book_url(book_name)

        if book_url:
            scraped_data = scrape_data(book_url)
            if scraped_data:
                save_data_json(scraped_data, filename_base)
            else:
                logging.error(f"Failed to scrape data for book URL: {book_url}")
        else:
            logging.error(f"Could not find a valid Goodreads URL for the book: {book_name}")

    except Exception as e:
        logging.error(f"A critical error occurred in main execution: {e}")
        import traceback
        logging.error(traceback.format_exc())

    finally:
        logging.info("--- Scraper finished ---")

if __name__ == "__main__":
    main()