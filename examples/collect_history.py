#!/usr/bin/env python3

import requests
import ujson as json
import sys
import time
import redis, hiredis
import sqlite3
import logging
import luminati as lm
from queue import Queue
import threading
logging.basicConfig(level=logging.INFO)


class stocktwits:

    def __init__(self):

        self.BASE_URL = "https://api.stocktwits.com/api/2/"
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.RETRY_LIMIT = 5
        self.session=lm.session('lum-customer-hl_32a41c02-zone-static',"zkw3ssluxun2")

    def streams(self, ticker=None, streams_type="symbol", **kwargs):
        '''Method to fetch posts for a particular ticker symbol'''
        params = {}
        params = kwargs
        if streams_type == "symbol":
            POSTS_URL = f"{self.BASE_URL}streams/symbol/{ticker}.json"
        elif streams_type == "trending":
            POSTS_URL = f"{self.BASE_URL}streams/trending.json"
        retries = self.RETRY_LIMIT

        while retries:
            logging.debug(f"{self.rate_limit_remaining} API calls remaining.")
            if self.rate_limit_remaining is not None and self.rate_limit_remaining < 1:
                wait_time_in_seconds = (self.rate_limit_reset - int(time.time())) + 1
                logging.info(f"Rate limit exhausted. Sleeping for {wait_time_in_seconds:,} seconds until next rate limit window.")
                time.sleep(wait_time_in_seconds)
            try:
                r = self.session.get(f"{POSTS_URL}", params=params)
            except requests.exceptions.ProxyError as e:
                retries -= 1
                continue
            response_headers = r.headers
            if 'X-RateLimit-Remaining' in response_headers:
                '''Sometimes the response headers do not have the rate-limit information so we need to check
                that they exist and if they don't, manually adjust the number of API calls remaining.'''
                self.rate_limit_remaining = int(response_headers['X-RateLimit-Remaining'])
                self.rate_limit_reset = int(response_headers['X-RateLimit-Reset'])
            else:
                if self.rate_limit_remaining is not None:
                    self.rate_limit_remaining -= 1
            if r.ok:
                return r.json()
            elif r.status_code == 429:
                self.rate_limit_remaining = 0
            else:
                logging.warning(f"Failed request. Received status code: {r.status_code}.")
                retries -= 1

def create_sqlite_db(db_name):

    conn = sqlite3.connect(f"/dev/shm/{db_name}.db",timeout=60.0)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS post (id INT PRIMARY KEY, ticker TEXT, data TEXT)')
    c.execute('PRAGMA journal_mode = wal')
    return conn

def get_min_id_for_ticker(c, ticker):

    c.execute('SELECT min(id) FROM post WHERE ticker = ?', (ticker,))
    id = c.fetchone()
    if id is None:
        return None
    else:
        return id[0]

def get_top_symbols(n=25):

    c = db.cursor()
    c.execute(f"SELECT symbol FROM symbol ORDER BY watchlist_count DESC LIMIT {int(n)}")
    symbols = c.fetchall()
    return [symbol[0] for symbol in symbols]


def fetch_posts(q):

    st = stocktwits()
    red = redis.StrictRedis(host='localhost', port=6379, db=0)
    db = create_sqlite_db("stocktwits")
    cur = db.cursor()

    while True:
        ticker = queue.get()
        if ticker is None:
            return
        min_id = get_min_id_for_ticker(cur, ticker)
        count = 0

        while True:
            data = st.streams(ticker=ticker, streams_type="symbol", max=min_id)
            retrieved_utc = int(time.time())
            messages = data['messages']
            created_at = None

            if not messages:
                break

            for message in messages:
                id = message['id']
                message['retrieved_utc'] = retrieved_utc
                created_at = message['created_at']

                json_data = json.dumps(message, ensure_ascii=False, escape_forward_slashes=False)
                #cur.execute("INSERT OR IGNORE INTO post (id, ticker, data) VALUES (?,?,?)", (id, ticker, json_data))
                red.set(f"stocktwits:post:{ticker}:{id}", json_data)
                if min_id is None or id < min_id:
                    min_id = id

            logging.info(f"Symbol: {ticker} -- Current date position: {created_at} | ID: {min_id:,} | Rate-limit remaining: {st.rate_limit_remaining:,}.")

            count += 1

            if count >= 250:
                break


NUMBER_OF_WORKERS = 3 # 25
threads = []
queue = Queue(maxsize=NUMBER_OF_WORKERS+1)

logging.info("Setting up workers.")
for x in range(NUMBER_OF_WORKERS):
    t = threading.Thread(target=fetch_posts, args=(queue,))
    threads.append(t)
    t.start()

db = create_sqlite_db("stocktwits")
cur = db.cursor()
top_symbols = get_top_symbols(5000)
print(top_symbols)

# for symbol in top_symbols:
#     queue.put(symbol)

# for x in range(NUMBER_OF_WORKERS):
#     queue.put(None)

# for thread in threads:
#     thread.join()