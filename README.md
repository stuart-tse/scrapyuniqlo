# Uniqlo Reviews Scraper

This project contains a Scrapy spider for scraping product reviews from Uniqlo's official website. It aims to extract detailed review information such as product IDs, review IDs, comments, ratings, and more, storing the data in MongoDB for further analysis.

## Project Structure

- `review_scraper/`: Main directory for the Scrapy project.
  - `spiders/`: Contains the spider for scraping reviews.
  - `items.py`: Defines the data structure for scraped items.
  - `middlewares.py`: Contains custom middleware for request processing.
  - `pipelines.py`: Includes processing pipelines to handle scraped data.
  - `settings.py`: Configuration file for the Scrapy project.
- `utils/`: Utility functions and classes, including MongoDB handler.
- `.env`: Environment variables for database connections and other configurations.
- `requirements.txt`: Required Python packages for the project.

## Setup

### Prerequisites

- Python 3.6+
- MongoDB
- A `.env` file configured with your MongoDB connection string and other necessary environment variables.

### Installation

1. Clone the repository:

sh
git clone https://github.com/yourusername/uniqlo-review-scraper.git
cd uniqlo-review-scraper
Install the required packages:
sh
Copy code
pip install -r requirements.txt
Configuration
Ensure your .env file is set up with the necessary variables, such as:

makefile
Copy code
MONGO_URL=mongodb://localhost:27017
FORCE_DROP_COLLECTION=True
Usage

To start the review scraping process, run:

Copy code
scrapy crawl reviewSpider
Features

Scrapes product reviews from Uniqlo's website.
Handles pagination to collect reviews from multiple pages.
Saves scraped data to MongoDB for persistence and analysis.
Provides utility functions for date-time operations and MongoDB handling.
Allows conditional execution based on the latest scrape time to avoid unnecessary scraping.
Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have suggestions for improvements or have identified bugs.
