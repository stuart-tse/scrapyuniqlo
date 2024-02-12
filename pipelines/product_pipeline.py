import os

import pymongo
import pymongo.errors
from dotenv import load_dotenv
from itemadapter import ItemAdapter
from ..utils.utils import Utils

class ProductPipeline:
    collection_name = 'products'

    def __init__(self, mongo_url, mongo_db):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        dotenv_path = os.path.join(project_root,'uniqloReview', '.env')

        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)

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
                self.update_prices(item_dict)
            except pymongo.errors.DuplicateKeyError:
                spider.duplicates_found = True
        return item

    def update_prices(self, item_dict):
        """
        Update the prices for product
        :param item_dict: item dictionary
        """
        product_id = item_dict.get('product_id')
        existing_product = self.collection.find_one({'product_id': product_id})
        if existing_product:
            self.add_new_price(existing_product, item_dict)
        else:
            self.insert_new_product(item_dict)

    def add_new_price(self, existing_product, item_dict):
        """
        Add a new price to the existing product
        :param existing_product:
        :param item_dict:
        """
        new_price_info = self.format_price_info(item_dict['prices'])
        last_price_entry = existing_product['prices'][-1] if 'prices' in existing_product and existing_product['prices'] else None

        # if last price is different from the new price and last price date is > 86400s
        if last_price_entry and last_price_entry['price'] != new_price_info[0]['price'] and \
                (Utils.get_datetime() - last_price_entry['date']) >= 86400:
            self.db[self.collection_name].update_one(
                {'product_id': existing_product['product_id']},
                {'$push': {'prices': {'$each': new_price_info}}}
            )

    def insert_new_product(self, item_dict):
        """
        Insert a new product into the database
        :param item_dict:
        """
        item_dict['prices'] = self.format_price_info(item_dict.get('prices',[]))
        self.collection.insert_one(item_dict)

    def format_price_info(self, prices):
        """
        Format the price information
        :param prices: the price information, either a single price or a list of prices
        :return: formatted price information as a list of dictionaries with date and price
        """
        current_date = Utils.get_datetime()
        if not isinstance(prices, list):
            formatted_prices = [{"date": current_date, "price": prices}]
        else:
            formatted_prices = [{"date": current_date, "price": price} for price in prices]
        return formatted_prices


