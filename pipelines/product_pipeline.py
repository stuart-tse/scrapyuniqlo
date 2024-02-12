import os

import pymongo
import pymongo.errors
from dotenv import load_dotenv
from itemadapter import ItemAdapter

class ProductPipeline:
    collection_name = 'products'

    def __init__(self, mongo_url, mongo_db):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        donenv_path = os.path.join(project_root, '.env')

        if os.path.exists(donenv_path):
            load_dotenv(donenv_path)

        mongo_url = os.getenv('MONGO_URL')

        if not mongo_url:
            raise EnvironmentError('MONGO_URL is not set')

        mongo_db = os.getenv('MONGO_DB', 'uniqlo')
        return cls(mongo_url, mongo_db)

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]
        self.collection = self.db[self.collection_name]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if item.__class__.__name__ == 'ProductItem':
            try:
                item_dict = ItemAdapter(item).asdict()
                self.collection.insert_one(item_dict)
            except pymongo.errors.DuplicateKeyError:
                spider.duplicates_found = True
        return item