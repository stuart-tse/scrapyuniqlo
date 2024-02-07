import scrapy
import json
import os
from scrapy.exceptions import CloseSpider
from dotenv import load_dotenv

from ..items import ReviewItem  # Make sure this import matches your project structure
from ..utils.utils import Utils
from ..utils.utils import MongoDBHandler


class ReviewScraperSpider(scrapy.Spider):
    name = "reviewSpider"
    allowed_domains = ["www.uniqlo.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reviews_scraped = 0
        self.max_reviews_to_scrape = 100
        self.setup_mongodb()
        self.latest_scraped_time = self.mongodb_handler.fetch_latest_scraped_time('reviews')
        self.start_urls = self.mongodb_handler.fetch_start_urls('products')
        print(f"Start urls: {self.start_urls}")

    def setup_mongodb(self):
        load_dotenv()
        mongo_url = os.getenv('MONGO_URL')
        if not mongo_url:
            raise CloseSpider('MONGO_URL is not set')
        self.mongodb_handler = MongoDBHandler(mongo_url)
        if os.getenv('FORCE_DROP_COLLECTION') == 'True':
            self.force_to_drop_collection()

    def start_requests(self):
        if self.latest_scraped_time and Utils.get_datetime() - self.latest_scraped_time < 86400:
            self.logger.info('Latest reviews are less than a day ago. Exiting spider.')
            print('Latest reviews are less than a day ago. Exiting spider.')
            return
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_review)

    def force_to_drop_collection(self):
        self.mongodb_handler.drop_collection('reviews')
        self.logger.info('Dropped the reviews collection')
        return True

    def parse_review(self, response):
        data = json.loads(response.text)
        product_id = response.meta.get('product_id') or self.extract_product_id_from_url(response.url)
        if product_id is None:
            self.logger.error('Product ID is None')
            return
        yield from (
            self.process_reviews(data, product_id))
        yield from self.handles_pagination(data, product_id)

    def extract_product_id_from_url(self, url):
        self.parts = url.split('/')
        try:
            product_id_index = self.parts.index('products') + 1
            return self.parts[product_id_index]
        except (ValueError, IndexError):
            self.logger.error('Product ID not found in the URL')
            return None


    def process_reviews(self, data, product_id):
        reviews = data.get('result', {}).get('reviews', [])
        for review in reviews:
            if self.reviews_scraped >= self.max_reviews_to_scrape:
                raise CloseSpider('Reached max reviews to scrape')
            self.reviews_scraped += 1
            yield self.extract_review_data(review, product_id)

    def extract_review_data(self, review, product_id):
        return ReviewItem(
            product_id=product_id,
            review_id=review.get('reviewId'),
            purchased_size=review.get('purchasedSize'),
            comment=review.get('comment'),
            fit=review.get('fit'),
            gender=review.get('gender'),
            location=review.get('location'),
            review_name=review.get('name'),
            rate=review.get('rate'),
            title=review.get('title'),
            created_date=review.get('createDate'),
            scraped_time=Utils.get_datetime()
        )

    def handles_pagination(self, data, product_id):
        pagination = data.get('result', {}).get('pagination', {})
        total_reviews = pagination.get('total', 0)
        offset = pagination.get('offset', 0) + 5

        if offset < total_reviews and product_id is not None:
            next_page = f'https://www.uniqlo.com/jp/api/commerce/v5/ja/products/{product_id}/reviews?limit=5&offset={offset}&sort=submission_time&httpFailure=true'
            yield scrapy.Request(next_page, callback=self.parse_review, meta={'product_id': product_id})

    def close_spider(self, spider):
        self.mongodb_handler.close_client()
