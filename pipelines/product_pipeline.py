import os

import pymongo
import pymongo.errors
from dotenv import load_dotenv

from ..client import OpenAiApiClient

load_dotenv()


class ProductPipeline(object):

    def __init__(self):
        # Check if all necessary environment variables are set
        try:
            self.open_api_key = os.getenv('OPENAI_API_KEY')
        except Exception as e:
            raise EnvironmentError('OPENAI_API_KEY is not set')
        self.translation_assistant = os.getenv('TRANSLATION_ASSISTANT')
        self.mongo_url = os.getenv('MONGO_URL')
        if not all([self.translation_assistant, self.open_api_key, self.mongo_url]):
            raise EnvironmentError('One or more environment variables are not set')
        self.translator = OpenAiApiClient(self.open_api_key, self.translation_assistant)

    def open_spider(self, spider):
        # Establish MongoDB connection
        try:
            self.client = pymongo.MongoClient(os.getenv('MONGO_URL'))
            self.db = self.client.uniqlo  # Use 'uniqlo' as the database name
        except pymongo.errors.ConnectionFailure as e:
            raise ConnectionError(f'Failed to connect to MongoDB: {e}')
        # Create or get collections
        self.products_collection = self.db.products

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Logic to process product items
        return item
