import threading
import queue
import time

import http.client

import os.path
from pathlib import Path

from bs4 import BeautifulSoup

class SourceRetriever:

    def __init__(self, baseURL, useCached = False, cacheDir = None, suffix = None):
        self.thread = threading.Thread(target = self._run_thread, daemon = True)
        self.todo = queue.Queue()
        self.responses = queue.Queue()
        self.docs = {}
        self.queued = set()
        self.useCached = useCached
        self.cacheDir = cacheDir
        if useCached:
            Path(cacheDir).mkdir(parents = True, exist_ok = True)

        self.baseURL = baseURL
        self.suffix = suffix
        self.thread.start()


    def _run_thread(self):
        conn = http.client.HTTPSConnection(self.baseURL)
        while True:
            url = self.todo.get()
            fullUrl = url
            if self.suffix:
                fullUrl = self.suffix + fullUrl
            print("Downloading ", fullUrl)
            conn.request("GET", fullUrl)
            resp = conn.getresponse()
            if resp.status != 200:
                print(resp.status, resp.reason)
                self.responses.put((url, None, Exception("Could not get source for " + url)))
                break
            result = resp.read()
            self.responses.put((url, result.decode(encoding = "utf8"), None))
            time.sleep(0.2)


    def get(self, url):
        url = url.split("#")[0]

        result = self.docs.get(url)
        if result:
            return result
        cachedPath = os.path.join(self.cacheDir, url)
        if self.useCached and os.path.exists(cachedPath):
            with open(cachedPath, 'r', encoding = "utf8") as r:
                soup = BeautifulSoup(r.read(), "html.parser")
                self.docs[url] = soup
                return soup

        if url not in self.queued:
            self.queued.add(url)
            self.todo.put(url)

        while 1:
            response = self.responses.get()
            if response[2]:
                raise response[2]
            soup = BeautifulSoup(response[1], "html.parser")
            self.docs[response[0]] = soup
            if self.useCached:
                cachedPath = os.path.join(self.cacheDir, response[0])
                with open(cachedPath, 'w', encoding = "utf8") as w:
                    w.write(response[1])
            if response[0] == url:
                return soup

    def enqueue(self, url):
        url = url.split("#")[0]
        if url in self.docs:
            return
        if url in self.queued:
            return
        cachedPath = os.path.join(self.cacheDir, url)
        if self.useCached and os.path.exists(cachedPath):
            return
        self.queued.add(url)
        self.todo.put(url)