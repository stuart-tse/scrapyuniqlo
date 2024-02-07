# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UniqloreviewItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    product_id = scrapy.Field()
    item_name = scrapy.Field()
    prices = scrapy.Field()
    color_names = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    product_image = scrapy.Field()
    url = scrapy.Field()


class ReviewItem(scrapy.Item):
    product_id = scrapy.Field()
    review_id = scrapy.Field()
    height_range = scrapy.Field()
    weight_range = scrapy.Field()
    purchased_size = scrapy.Field()
    age_range = scrapy.Field()
    review_name = scrapy.Field()
    comment = scrapy.Field()
    fit = scrapy.Field()
    gender = scrapy.Field()
    location = scrapy.Field()
    rate = scrapy.Field()
    title = scrapy.Field()
    created_date = scrapy.Field()
    translated_title = scrapy.Field()
    translated_comment = scrapy.Field()
    scraped_time = scrapy.Field()

