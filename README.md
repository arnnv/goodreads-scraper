# Goodreads Book Scraper

This project provides tools to scrape book details and recent reviews from Goodreads. It includes both a command-line interface (CLI) script and a web application built with Streamlit.

## Features

*   **CLI Scraper:** Fetch book data directly from your terminal.
*   **Streamlit Web App:** Interactive interface to search for books and view scraped data.
*   **Data Extraction:** Scrapes essential book information:
    *   Title
    *   Author
    *   Average Rating
    *   Total Review Count
    *   Book Description
    *   Genres
    *   Recent Reviews (limited number, configurable in `scraper.py`)
*   **JSON Output:** Saves the scraped data to a structured JSON file in the `parsed_data/` directory.

## Installation

1.  **Clone the repository:**
    ```bash
    https://github.com/arnnv/goodreads-scraper.git
    cd goodreads-scraper
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Command-Line Interface (CLI)

Run the scraper script from your terminal:

```bash
python scraper.py -b "Your Book Title Here"
```

*   Replace `"Your Book Title Here"` with the actual title of the book you want to scrape (the default is "The Final Empire").
*   The scraped data will be saved as a JSON file in the `parsed_data` directory (e.g., `your_book_title_here_goodreads_data.json`).

### Streamlit Web Application

Launch the web app:

```bash
streamlit run app.py
```

*   This will open the application in your default web browser.
*   Enter a book title in the input field and click "Scrape Book Data".
*   The results will be displayed on the page, and the data will also be saved to a JSON file in the `parsed_data` directory.

## Dependencies

*   Python 3.x
*   requests
*   beautifulsoup4
*   lxml
*   streamlit

See `requirements.txt` for package details.

## Output

Scraped data is saved in JSON format within the `parsed_data` directory. The filename is derived from the book title (e.g., `the_final_empire_goodreads_data.json`).

Example JSON structure:

```json
{
    "url": "https://www.goodreads.com/book/show/...",
    "title": "The Final Empire",
    "author": "Brandon Sanderson",
    "rating": 4.48,
    "review_count": 945179,
    "description": "...",
    "genres": [
        "Fantasy",
        "Fiction",
        "High Fantasy",
        ...
    ],
    "reviews": [
        {
            "reviewer_name": "...",
            "review_text": "..."
        },
        ...
    ]
}
```

## Disclaimer

*   Web scraping is dependent on the structure of the target website (Goodreads). Changes to the Goodreads website may break this scraper. Ensure you have the latest browser user-agent string in `HEADERS` within `scraper.py` if you encounter issues.
*   Please use this tool responsibly and respect Goodreads' Terms of Service. Excessive scraping can overload their servers. The script includes a `POLITE_DELAY` between requests to mitigate this.
