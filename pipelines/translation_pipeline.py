from ..items import ReviewItem
from ..utils.openAIClient import OpenAiApiClient
import os


class TranslationPipeline:
    def __init__(self, client):
        self.client = client

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            client=OpenAiApiClient(
                api_key=os.getenv('OPENAI_API_KEY'),
                assistant_id=os.getenv('TRANSLATION_ASSISTANT')
            )
        )


    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        combined_text = "{} [SEP] {}".format(item['title'], item['comment'])
        translated_text = self.client.translate_japanese_concurrently(combined_text)
        translated_title, translated_content = translated_text.split("[SEP]")
        if translated_title and translated_content:
            item['translated_review_title'] = translated_title
            item['translated_review_comment'] = translated_content
        return item


    def combine_title_and_comments(self, item):
        return f"{item['review_title']} [SEP] {item['review_content']}"
