from datetime import datetime
from pymongo import MongoClient
class Utils:
    def __init__(self):
        pass
    @staticmethod
    def get_datetime():
        return int(datetime.now().timestamp())


class MongoDBHandler:
    def __init__(self, mongo_url, db_name='uniqlo'):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]

    def fetch_start_urls(self, collection_name='products'):
        start_urls = [collection_name['url'] for collection_name in self.db[collection_name].find({}, {'url': 1}) if 'url' in collection_name]
        return start_urls

    def close_client(self):
        self.client.close()

    def save_to_db(self, collection_name, data):
        self.db[collection_name].insert_one(data)
        return True

    def fetch_latest_scraped_time(self, collection_name):
        collection = self.db[collection_name]
        latest_scraped_time = collection.find_one({}, sort=[( 'scraped_time', -1)])
        if latest_scraped_time:
            return latest_scraped_time['scraped_time']
        else:
            return None

    # method to drop the collection
    def drop_collection(self, collection_name):
        self.db[collection_name].drop()
        return True

    def fetch_product_with_review_counts(self, product_id, collection_name='products'):
        """
        Fetch the product with review counts from the database
        :param collection_name: the name of the collection
        :param product_id: the id of the product
        :return: review count integer
        """
        # Fetch the product with review counts from the database and return the product review count integer
        review_count = self.db[collection_name].find_one({'product_id': product_id}, {'review_count': 1})
        return review_count['review_count']

    def count_reviews_in_db(self, product_id, collection_name='reviews'):
        """
        Count the number of reviews in the database
        :param product_id: the product id
        :param collection_name: the name of the collection
        :return: the number of reviews in the database
        """
        reviews_collection = self.db[collection_name]
        return reviews_collection.count_documents({'product_id': product_id})








