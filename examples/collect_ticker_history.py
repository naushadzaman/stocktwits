#!/usr/bin/env python3
import requests
import ujson as json
import time
import sqlite3
import logging
logging.basicConfig(level=logging.DEBUG)
class stocktwits:
    def __init__(self):
        self.BASE_URL = "https://api.stocktwits.com/api/2/"
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.RETRY_LIMIT = 5
    def posts(self, ticker, **kwargs):
        '''Method to fetch posts for a particular ticker symbol'''
        params = {}
        params = kwargs
        POSTS_URL = f"{self.BASE_URL}streams/symbol/"
        retries = self.RETRY_LIMIT
        while retries:
            logging.debug(f"{self.rate_limit_remaining} API calls remaining.")
            if self.rate_limit_remaining is not None and self.rate_limit_remaining < 1:
                wait_time_in_seconds = (self.rate_limit_reset - int(time.time())) + 1
                logging.info(f"Rate limit exhausted. Sleeping for {wait_time_in_seconds:,} seconds until next rate limit window.")
                time.sleep(wait_time_in_seconds)
            r = requests.get(f"{POSTS_URL}{ticker}.json", params=params)
            response_headers = r.headers
            self.rate_limit_remaining = int(response_headers['X-RateLimit-Remaining'])
            self.rate_limit_reset = int(response_headers['X-RateLimit-Reset'])
            if r.ok:
                return r.json()
            elif r.status_code == 429:
                self.rate_limit_remaining = 0
            else:
                logging.warning(f"Failed request. Received status code: {r.status_code}.")
                retries -= 1
def create_sqlite_db(db_name):
    conn = sqlite3.connect(f"{db_name}.db",timeout=60.0)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS post (id INT PRIMARY KEY, ticker TEXT, data TEXT)')
    c.execute('PRAGMA journal_mode = wal')
    return conn
db = create_sqlite_db("stocktwits")
cur = db.cursor()
st = stocktwits()
# Fetch historical posts for a specific ticker
min_id = None
ticker = "SRNE"
while True:
    data = st.posts(ticker=ticker, max=min_id)
    symbol = data['symbol']
    messages = data['messages']
    for message in messages:
        id = message['id']
        json_data = json.dumps(message, ensure_ascii=False, escape_forward_slashes=False)
        cur.execute("INSERT OR IGNORE INTO post (id, ticker, data) VALUES (?,?,?)", (id, ticker, json_data))
        if min_id is None or id < min_id:
            min_id = id
        logging.debug(f"Inserted post id {id} into post table.")
    db.commit()
