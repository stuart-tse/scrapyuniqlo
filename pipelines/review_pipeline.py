import logging
import pymongo
from scrapy.exceptions import NotConfigured
from itemadapter import ItemAdapter
from dotenv import load_dotenv
import os

class ReviewPipeline:
    def __init__(self):
        load_dotenv()
        mongo_url = os.getenv('MONGO_URL')
        if not mongo_url:
            raise NotConfigured('MONGO_URL environment variable is not set')
        self.mongo_url = mongo_url

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client.uniqlo  # Adjust database name as needed
        self.reviews_collection = self.db.reviews

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Ensure this pipeline only processes ReviewItem objects
        print(f"Came to process_item in review_pipeline.py")
        if item.__class__.__name__ == 'ReviewItem':
            self._process_review_item(item)
        else:
            logging.warning(f"ReviewPipeline encountered an unexpected item type: {item.__class__.__name__}")
        return item

    def _process_review_item(self, review_item):
        print(f"Processing review: {review_item.get('review_id')}")
        # Convert the item to a dict and insert into the reviews collection
        review_dict = ItemAdapter(review_item).asdict()
        self.reviews_collection.insert_one(review_dict)
        logging.info(f"Inserted review: {review_dict.get('review_id')}")
