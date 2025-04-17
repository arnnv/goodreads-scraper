import streamlit as st
import scraper # Import the scraper functions
import os # Import os module

# --- Streamlit App Configuration ---
st.set_page_config(page_title="Goodreads Scraper", layout="wide")

st.title("📚 Goodreads Book Scraper")
st.caption("Enter a book title to fetch its details and recent reviews from Goodreads.")

# --- Input Section ---
default_book = scraper.DEFAULT_BOOK_NAME
book_name_input = st.text_input("Enter Book Title:", value=default_book)

# --- Scraping Execution ---
if st.button("Scrape Book Data"):
    if not book_name_input:
        st.warning("Please enter a book title.")
    else:
        with st.spinner(f"Searching for '{book_name_input}' and scraping data..."):
            try:
                # 1. Get Book URL
                st.info(f"Searching for the book URL for '{book_name_input}'...")
                book_url = scraper.get_book_url(book_name_input)

                if book_url:
                    st.info(f"Found book URL: {book_url}. Now scraping details...")
                    # 2. Scrape Data
                    scraped_data = scraper.scrape_data(book_url)

                    if scraped_data:
                        st.success("Successfully scraped data!")

                        # --- Save Data to JSON ---
                        try:
                            # Generate filename base similar to the CLI script
                            filename_base = book_name_input.lower().replace(' ', '_').replace(':', '').replace('\'', '').replace('/', '').replace('\\', '')[:50]
                            scraper.save_data_json(scraped_data, filename_base)
                            # Get the expected filename to show the user
                            json_filename = f"{filename_base}_goodreads_data.json"
                            json_filepath = os.path.join("parsed_data", json_filename) # Construct full path
                            st.info(f"Data also saved to {json_filepath}") # Show full path
                        except Exception as save_e:
                            st.warning(f"Could not save data to JSON file: {save_e}")

                        # --- Display Results ---
                        st.header(f"Book Details: {scraped_data.get('title', 'N/A')}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Author")
                            st.write(scraped_data.get('author', 'N/A'))
                            st.subheader("Rating")
                            st.write(f"{scraped_data.get('rating', 'N/A')} / 5")
                        with col2:
                            st.subheader("Review Count")
                            st.write(f"{scraped_data.get('review_count', 'N/A'):,}") # Format with commas
                            st.subheader("Genres")
                            genres = scraped_data.get('genres', [])
                            if genres:
                                st.write(", ".join(genres))
                            else:
                                st.write("N/A")

                        st.subheader("Description")
                        # Use markdown for better formatting, ensure newlines are handled
                        description_text = scraped_data.get('description', 'N/A')
                        st.markdown(description_text.replace('\n', '\n\n'))

                        st.subheader(f"Recent Reviews (Up to {scraper.MAX_REVIEWS_TO_SCRAPE})")
                        reviews = scraped_data.get('reviews', [])
                        if reviews:
                            for i, review in enumerate(reviews):
                                with st.expander(f"Review {i+1} by {review.get('reviewer_name', 'Unknown User')}"):
                                    st.write(review.get('review_text', 'No text found.'))
                        else:
                            st.info("No reviews were found or scraped for this book.")

                    else:
                        st.error(f"Failed to scrape data for the book URL: {book_url}. The page structure might have changed, or the content might be loaded dynamically.")

                else:
                    st.error(f"Could not find a valid Goodreads URL for the book: '{book_name_input}'. Please check the title or try a different one.")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.exception(e) # Show traceback in the app for debugging 