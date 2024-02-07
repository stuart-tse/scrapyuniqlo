import time
from openai import OpenAI, OpenAIError
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging


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

    def translate_japanese(self, text, max_retry=3):
        retry_count = 0
        while retry_count < max_retry:
            with self.lock:
                current_time = int(time.time())
                if current_time - self.last_request_time >= 60:
                    self.request_count = 0
                    self.last_request_time = current_time

                if self.request_count >= 60:
                    time.sleep(60 - (current_time - self.last_request_time))

                self.request_count += 1
            try:
                logging.info(f"Translating: {text}")
                thread = self.client.beta.threads.create()
                message = self.client.beta.threads.messages.create(thread_id=thread.id, role="user", content=text)
                run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=self.assistant_id)

                while run.status == "in_progress" or run.status == "queued":
                    time.sleep(1)
                    run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                if run.status == "completed":
                    messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for message in messages.data:
                        if message.role == "assistant":
                            return message.content[0].text.value
            except OpenAIError as e:
                if e.__getattribute__('status_code') == 429:
                    retry_count += 1
                    logging.info('Too many requests, waiting for reset')
                    time.sleep(10)  # wait for 10 seconds
                    print('Too many requests, waiting for reset')
                else:
                    retry_count += 1
                    if retry_count >= max_retry:
                        logging.error("Max Retries Reached, Translation Failed: {e}")
                        break

        return "Translation failed"

    def translate_japanese_concurrently(self, texts, max_worker=10):
        results = [None] * len(texts)

        with ThreadPoolExecutor(max_workers=max_worker) as executor:
            future_to_index = {executor.submit(self.translate_japanese, text): i for i, text in enumerate(texts)}
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                    print(f'Task {index + 1}/{len(texts)} completed')
                except Exception as e:
                    results[index] = "Translation failed"
                    print(f'Error in task {index + 1}: {e}')

        # order results by index
        ordered_results = [results[i] for i in range(len(results))]
        return ordered_results
