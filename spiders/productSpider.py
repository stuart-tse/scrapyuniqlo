import scrapy
import pymongo, pymongo.errors
from scrapy.exceptions import CloseSpider
from dotenv import load_dotenv


import os
import json
from ..items import ProductItem
from ..utils.utils import Utils

class ProductSpiderSpider(scrapy.Spider):
    name = 'productSpider'
    allowed_domains = ['www.uniqlo.com']
    start_urls = [
        "https://www.uniqlo.com/jp/api/commerce/v5/ja/products?path=%2C%2C1641&categoryId=1641&offset=0&limit=72&httpFailure=true"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = self.setup_mongodb()

    def setup_mongodb(self):
        load_dotenv()
        mongo_url = os.getenv('MONGO_URL')
        if not mongo_url:
            raise CloseSpider('MONGO_URL is not set')
        self.client = pymongo.MongoClient(mongo_url)
        self.db = self.client.uniqlo
        self.products_collection = self.db.products

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(os.getenv('MONGO_URL'))
            self.db = self.client.uniqlo  # Use 'uniqlo' as the database name
        except pymongo.errors.ConnectionFailure as e:
            raise ConnectionError(f'Failed to connect to MongoDB: {e}')
        # Create or get collections
        self.products_collection = self.db.products

    def close_spider(self, spider):
        self.client.close()

    def parse(self, response):
        """
        Parse the response and extract the product data
        :param response: the fetched response from the start_urls
        :return: json data of the products
        """

        data = json.loads(response.text)
        products = data.get('result', {}).get('items', {})
        for product in products:
            product_data = self.extract_product_data(product)
            self.save_to_db(product_data)

    def extract_product_data(self, product):

        return ProductItem(
            product_id=product.get('productId'),
            item_name=product.get('name'),
            prices=self.get_price_date_pair(product),
            color_names=[color.get('name') for color in product.get('colors', [])],
            rating=product.get('rating', {}).get('average'),
            review_count=product.get('rating', {}).get('count'),
            product_image=next(iter(product.get('images', {}).get('main', {}).values()), {}).get('image', 'No Image'),
            url=f"https://www.uniqlo.com/jp/api/commerce/v5/ja/products/{product.get('productId')}/reviews?limit=5&offset=0&sort=submission_time&httpFailure=true"
        )



    def extract_colors(self, product):

        # Extract the color names from the product data
        colors = product.get('colors', {})
        color_names = []
        for color in colors:
            color_name = color.get('name')
            color_names.append(color_name)
        return color_names

    def save_to_db(self, product_data):
        """
        Save the product data to the database with new price information only if the date is different
        :param product_data: ProductItem or dict
        :return: None (No return value) and save product data to the database
        """

        product_dict = dict(product_data) if isinstance(product_data, ProductItem) else product_data
        existing_product = self.fetch_existing_product(product_dict['product_id'])

        if existing_product:
            self.update_price_if_new_date(existing_product, product_dict)
        else:
            self.insert_new_price(product_dict)

        self.products_collection.update_one({'product_id': product_dict['product_id']}, {'$set': product_dict},
                                            upsert=True)


    def fetch_existing_product(self, product_id):
        """
        Fetch the existing product from the database
        :param product_id: product_id of the product id
        :return: product data if the product exists, None otherwise
        """
        return self.products_collection.find_one({'product_id': product_id})

    def update_price_if_new_date(self, existing_product, new_product):
        """
        Update the product data if the date is different
        :param existing_product: Existing product data from the database
        :param new_product: New product data
        :return: None (No return value) and update the product data if the date is different
        """
        current_scrape_date = Utils.get_datetime()
        # Get the last price entry if available else None
        last_price_entry = existing_product['prices'][-1] if 'prices' in existing_product and existing_product['prices'] \
            else None

        if not last_price_entry or last_price_entry[1] != current_scrape_date:
            self.products_collection.update_one(
                {'product_id': existing_product['product_id']},
                {'$push': {'prices': self.get_price_date_pair(new_product)}},
            )

    def insert_new_price(self, product_dict):
        """
        Insert new product data to the database
        :param product_dict: Product data to be inserted
        :return: None (No return value) and insert new product data to the database
        """
        self.products_collection.update_one({'product_id': product_dict['product_id']},
                                            {'$push': {'prices': self.get_price_date_pair(product_dict)}},
                                            upsert=True)

    def get_price_date_pair(self, product):
        base_price = product.get('prices', {}).get('base', {}).get('value')
        promo_price = product.get('prices', {}).get('promo', {}).get('value') if product.get('prices', {}).get('promo') else None
        final_price = promo_price if promo_price else base_price
        return {"date": Utils.get_datetime(), "price": final_price}

