import time
from openai import OpenAI, OpenAIError
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class OpenAiApiClient:
    def __init__(self, api_key, assistant_id):
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.client = OpenAI(
            api_key=self.api_key,
        )
        self.last_request_time = time.time()
        self.lock = Lock()
        self.request_count = 0

    def handle_rate_limit(self):
        current_time = int(time.time())
        # Reset the request count if it has been 60 seconds since the last request
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
        # If the request count is greater than or equal to 60, wait until the next minute
        if self.request_count >= 60:
            time.sleep(60 - (current_time - self.last_request_time))
        # Increment the request count for every request
        self.request_count += 1

    def handle_error(self, e):
        if e.__getattribute__('status_code') == 429:
            print('Too many requests, waiting for reset')
        else:
            print(f'An error occurred: {e}')

    def create_thread(self):
        return self.client.beta.threads.create()

    def create_message(self, thread_id, role, content):
        return self.client.beta.threads.messages.create(thread_id=thread_id, role=role, content=content)

    def create_run(self, thread_id: str, assistant_id: str):
        return self.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    def create_and_send_message(self, text: str) -> str:
        thread = self.create_thread()
        self.create_message(thread.id, "user", text)
        return thread.id

    def wait_for_completion_and_fetch_result(self, thread_id: str) -> str:
        run = self.create_run(thread_id, self.assistant_id)
        while run.status == "in_progress" or run.status == "queued":
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status == "completed":
                return self.fetch_translated_text(thread_id)



    def fetch_translated_text(self, thread_id):
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value

    def translate_japanese(self, text, max_retry=3):
        retry_count = 0
        while retry_count < max_retry:
            self.handle_rate_limit()
            try:
                thread_id = self.create_and_send_message(text)
                translated_text = self.wait_for_completion_and_fetch_result(thread_id)
                if translated_text:
                    return translated_text
            except OpenAIError as e:
                self.handle_error(e)
            retry_count += 1
        return None

    def translate_japanese_concurrently(self, texts, max_retry=3):
        results = [None] * len(texts)
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(self.translate_japanese, text, max_retry) for text in texts]
            for future in as_completed(futures):
                idx = futures.index(future)
                results[idx] = future.result()
        return results



