import logging
import pymongo, pymongo.errors
from scrapy.exceptions import NotConfigured, DropItem
from itemadapter import ItemAdapter
from dotenv import load_dotenv
from ..utils.openAIClient import OpenAiApiClient
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
        # Ensure unique index on review_id
        self.reviews_collection.create_index([('review_id', pymongo.DESCENDING)], unique=True)
        self.translate_client = OpenAiApiClient(
            api_key=os.getenv('OPENAI_API_KEY'),
            assistant_id=os.getenv('TRANSLATION_ASSISTANT')
        )

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Ensure this pipeline only processes ReviewItem objects
        if item.__class__.__name__ == 'ReviewItem':
            item = self.translate_text(item)
            self._process_review_item(item, spider)
        elif item.__class__.__name__ == 'ProductItem':
            pass
        else:
            logging.warning(f"ReviewPipeline encountered an unexpected item type: {item.__class__.__name__}")
            spider.duplicates_found = True
            raise DropItem(f"Duplicate review found: {item.get('review_id')}")

    def _process_review_item(self, review_item, spider):
        # Convert the item to a dict and insert into the reviews collection
        review_dict = ItemAdapter(review_item).asdict()
        try:
            self.reviews_collection.insert_one(review_dict)
            logging.warning(f"Inserted review: {review_dict.get('review_id')}")
        except pymongo.errors.DuplicateKeyError:
            logging.warning(f"Duplicate review found and skipping: {review_dict.get('review_id')}")
            spider.duplicates_found = True

    def drop_duplicates_review(self):
        pass

    def combine_title_and_comments(self, item):
        return f"{item['title']} [SEP] {item['comment']}"

    def translate_text(self, item):
        combined_text = self.combine_title_and_comments(item)
        if item.__class__.__name__ == 'ReviewItem' and not item.get('translated', False):
            try:
                translated_text = self.translate_client.translate_japanese(combined_text)
                translated_parts = translated_text.split("[SEP]")
                if len(translated_parts) == 2:
                    item['translated_review_title'] = translated_parts[0].strip()
                    item['translated_review_comment'] = translated_parts[1].strip()
                    item['translated'] = True
            except Exception as e:
                logging.error(f"Failed to translate review: {item.get('review_id')}, {e}")
        return item

    def is_duplicate(self, item):
        review_id = ItemAdapter(item).get('review_id')
        exists = self.reviews_collection.find_one({'review_id': review_id})
        if exists:
            return True
        return False

    def store_in_database(self, item):
        try:
            self.reviews_collection.insert_one(ItemAdapter(item).asdict())
            logging.info(f"Inserted review: {item.get('review_id')}")
        except pymongo.errors.DuplicateKeyError:
            logging.warning(f"Duplicate review found and skipping: {item.get('review_id')}")
            raise DropItem(f"Duplicate review found: {item.get('review_id')}")
